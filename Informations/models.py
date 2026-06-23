from datetime import datetime, timezone
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt as _bcrypt
from . import db


# ── Phase 4A: Fernet helper for at-rest encryption of HMAC secrets ───
# Derives a 32-byte key from SECRET_KEY via HKDF so we don't need a
# separate env var.  Cached per SECRET_KEY value.
_fernet_cache: dict = {}  # {secret_key_value: Fernet}


def _fernet():
    """Return a cached Fernet instance keyed by the app's SECRET_KEY."""
    import base64
    from flask import current_app
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    sk = current_app.config['SECRET_KEY']
    if sk not in _fernet_cache:
        derived = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ecopoints-qr-hmac-v1',
            info=b'qr_hmac_secret_enc',
        ).derive(sk.encode() if isinstance(sk, str) else sk)
        _fernet_cache[sk] = Fernet(base64.urlsafe_b64encode(derived))
    return _fernet_cache[sk]


# ============================================================================
# Group 1: Multi-Tenant Identity (The Core)
# ============================================================================

class OrgType(db.Model):
    """
    Lookup table for organization types (University, Corporation, HOA, etc.).
    Super-admin can add/delete types dynamically.
    """
    __tablename__ = 'org_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organizations = db.relationship('Organization', backref='org_type_ref', lazy=True)

    def __repr__(self):
        return f'<OrgType {self.name}>'


class Organization(db.Model):
    """
    The top-level tenant — a school, village, or corporation renting the system.
    Address and contact details are stored in separate tables (ORG_ADDRESS, ORG_CONTACT).
    """
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)              # Org Abbreviation
    full_name = db.Column(db.String(500))                         # Full Org Name
    type_id = db.Column(db.Integer, db.ForeignKey('org_types.id'), nullable=True, index=True)
    status = db.Column(db.String(20), default='Active')           # Active, Inactive
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    force_logout_at = db.Column(db.DateTime(timezone=True), nullable=True)  # Phase 4C: force-logout timestamp
    qr_hmac_secret_enc = db.Column(db.LargeBinary, nullable=True)  # Phase 4A: Fernet-encrypted HMAC secret

    # Relationships
    address = db.relationship('OrgAddress', backref='organization', uselist=False,
                              lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('OrgContact', backref='organization', lazy=True,
                               cascade='all, delete-orphan')
    community_groups = db.relationship('CommunityGroup', backref='organization', lazy=True,
                                       cascade='all, delete-orphan')
    rvms = db.relationship('RVM', backref='organization', lazy=True,
                           cascade='all, delete-orphan')
    rewards = db.relationship('Reward', backref='organization', lazy=True,
                              cascade='all, delete-orphan')
    notification_settings = db.relationship('NotificationSetting', backref='organization',
                                            lazy=True, cascade='all, delete-orphan')
    notification_logs = db.relationship('NotificationLog', backref='organization',
                                        lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Organization {self.name}>'

    def get_qr_hmac_secret(self) -> bytes:
        """Decrypt and return the per-org HMAC secret (Phase 4A)."""
        if not self.qr_hmac_secret_enc:
            raise ValueError(f'Organization {self.id} has no QR HMAC secret provisioned')
        return _fernet().decrypt(self.qr_hmac_secret_enc)

    @staticmethod
    def encrypt_qr_hmac_secret(plaintext: bytes) -> bytes:
        """Encrypt a plaintext HMAC secret for storage (Phase 4A)."""
        return _fernet().encrypt(plaintext)


class OrgAddress(db.Model):
    """
    1:1 address record for an Organization.
    Flat strings for each address component — no normalized city lookup.
    """
    __tablename__ = 'org_address'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, unique=True, index=True)
    street_address = db.Column(db.String(500))                    # House/Block/Lot/Street
    barangay = db.Column(db.String(200))
    city_municipality = db.Column(db.String(200))
    province = db.Column(db.String(200))
    region = db.Column(db.String(200))
    zip_code = db.Column(db.String(10))

    def __repr__(self):
        return f'<OrgAddress org={self.organization_id}>'


class OrgContact(db.Model):
    """
    Person-in-charge contact for an Organization.
    One org can have multiple contacts (1:N).
    """
    __tablename__ = 'org_contact'
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'email', name='uq_org_contact_email'),
        db.UniqueConstraint('organization_id', 'phone_number', name='uq_org_contact_phone'),
    )
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    first_name = db.Column(db.String(200))
    last_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<OrgContact {self.first_name} {self.last_name}>'


class CommunityGroup(db.Model):
    """
    Dynamic sub-groups for user classification (e.g. BSIT, STEM, IT Dept).

    A group carries its educational_level so the user form does not need to
    ask for it — selecting the group implies the level. year_level lives on
    the User (it changes yearly).

    educational_level values (University org type only):
      Kindergarten, Elementary, JHS, SHS, College. NULL for Corporate/Community.
    """
    __tablename__ = 'community_groups'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    abbreviation = db.Column(db.String(50))
    educational_level = db.Column(db.String(30), nullable=True)   # Kindergarten, Elementary, JHS, SHS, College
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = db.relationship('User', backref='community_group', lazy=True)

    def __repr__(self):
        return f'<CommunityGroup {self.abbreviation or self.name}>'


class User(db.Model):
    """
    A human who interacts with the system — admin or end-user.

    role values:
      Admin:    superadmin, head_admin, auditor, inventory_officer, technician
      End-user: user, dependent

    user_type (only for role='user'): 'student', 'faculty', 'staff'
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    community_group_id = db.Column(db.Integer, db.ForeignKey('community_groups.id'),
                                   nullable=False, index=True)
    display_id = db.Column(db.String(30), unique=True, nullable=True, index=True)
    qr_token = db.Column(db.String(100), unique=True, nullable=True, index=True, default=lambda: secrets.token_hex(16))

    # Identity (split name per ERD)
    first_name = db.Column(db.String(200), nullable=False)
    middle_name = db.Column(db.String(200), nullable=True)
    last_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(200), unique=True, nullable=True)
    phone = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Role & Classification
    role = db.Column(db.String(30), default='user', nullable=False, index=True)
    user_type = db.Column(db.String(30), nullable=True)           # student, alumni, faculty, staff, resident, employee, etc.
    year_level = db.Column(db.String(30), nullable=True)          # e.g. Grade 11, 3rd Year (student-only)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)        # When account was disabled
    avatar_url = db.Column(db.String(500), nullable=True)         # Profile avatar image
    last_username_change = db.Column(db.DateTime, nullable=True)  # 30-day cooldown enforcement

    # Consent
    terms_accepted_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    wallet = db.relationship('Wallet', backref='user', uselist=False,
                             lazy=True, cascade='all, delete-orphan')
    security = db.relationship('UserSecurity', backref='user', uselist=False,
                               lazy=True, cascade='all, delete-orphan')
    otp_codes = db.relationship('OtpCode', backref='user', lazy=True,
                                cascade='all, delete-orphan')
    maintenance_logs = db.relationship('MaintenanceLog', backref='performed_by', lazy=True,
                                       foreign_keys='MaintenanceLog.performed_by_id')
    admin_logs = db.relationship('AdminLog', backref='admin', lazy=True,
                                  foreign_keys='AdminLog.admin_user_id')
    bulk_deposits = db.relationship('BulkDeposit', backref='admin_user', lazy=True,
                                    foreign_keys='BulkDeposit.admin_user_id')

    # ── Backward-compat property: controllers use user.name everywhere ──
    @property
    def name(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts)

    def set_password(self, password):
        # Pin the algorithm explicitly so stored hashes are reproducible
        # across Werkzeug/Python versions. scrypt is the current Werkzeug
        # default, so this is a no-op for existing hashes (no migration
        # needed) — it only guards against a future default change.
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role in ('superadmin', 'head_admin', 'auditor',
                             'inventory_officer', 'technician')

    # ── Role prefix map for display_id ──
    ROLE_PREFIX = {
        'superadmin': 'SA',
        'head_admin': 'HEAD',
        'auditor': 'AUD',
        'inventory_officer': 'INV',
        'technician': 'TECH',
        'user': 'USER',
        'dependent': 'DEP',
    }

    @staticmethod
    def generate_display_id(role, org_abbreviation):
        """Generate next display_id like USER-AU-001."""
        prefix = User.ROLE_PREFIX.get(role, 'USER')
        abbr = (org_abbreviation or 'SYS').upper()
        pattern = f'{prefix}-{abbr}-%'

        last = db.session.query(User).filter(User.display_id.like(pattern))\
            .order_by(User.display_id.desc()).first()

        if last and last.display_id:
            try:
                seq = int(last.display_id.rsplit('-', 1)[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f'{prefix}-{abbr}-{seq:03d}'

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name} ({self.role})>'

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.qr_token:
            self.qr_token = secrets.token_hex(16)


class Wallet(db.Model):
    """
    Point wallet — strict 1:1 with User.
    Tracks current balance, lifetime total (for leaderboards), and streak.
    """
    __tablename__ = 'wallet'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False, unique=True, index=True)
    points_balance = db.Column(db.Integer, default=0)
    lifetime_points = db.Column(db.Integer, default=0)            # Total ever earned
    streak = db.Column(db.Integer, default=0)                     # Consecutive recycling days
    best_streak = db.Column(db.Integer, default=0)               # All-time highest streak
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    transactions = db.relationship('Transaction', backref='wallet', lazy=True)
    sessions = db.relationship('RecyclingSession', backref='wallet', lazy=True)
    redemptions = db.relationship('RewardRedemption', backref='wallet', lazy=True)
    bulk_deposits = db.relationship('BulkDeposit', backref='wallet', lazy=True,
                                    foreign_keys='BulkDeposit.wallet_id')

    def __repr__(self):
        return f'<Wallet user={self.user_id} | {self.points_balance} pts>'


class UserSecurity(db.Model):
    """
    Two-factor authentication settings for a user.
    Strict 1:1 with User.
    """
    __tablename__ = 'user_security'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False, unique=True, index=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    preferred_method = db.Column(db.String(20), nullable=True)    # email, sms, authenticator
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserSecurity user={self.user_id} 2FA={"on" if self.two_factor_enabled else "off"}>'


class OtpCode(db.Model):
    """
    Persistent OTP codes for two-factor authentication.
    Replaces the old in-memory OTP store.
    """
    __tablename__ = 'otp_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)         # Hashed 6-digit code
    sent_to = db.Column(db.String(200), nullable=False)           # Email or phone
    channel = db.Column(db.String(10), nullable=False)            # email, sms
    is_used = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)                   # Wrong-code attempt counter
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<OtpCode user={self.user_id} used={self.is_used}>'


# ============================================================================
# Group 2: Hardware & IoT (RVM Operations)
# ============================================================================

class RVM(db.Model):
    """
    A physical Reverse Vending Machine (Raspberry Pi).
    """
    __tablename__ = 'rvms'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    machine_uuid = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    location_name = db.Column(db.String(200), nullable=True)      # Area placement
    is_capacity_full = db.Column(db.Boolean, default=False)       # Status from IR Sensor
    is_online = db.Column(db.Boolean, default=False)
    api_key_hash = db.Column(db.String(255), nullable=True)       # Phase 4A: BCrypt hash of API key
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = db.relationship('RecyclingSession', backref='rvm', lazy=True)
    maintenance_logs = db.relationship('MaintenanceLog', backref='rvm', lazy=True)

    def verify_api_key(self, plaintext: str) -> bool:
        """Constant-time compare plaintext API key against stored BCrypt hash (Phase 4A)."""
        if not self.api_key_hash:
            return False
        try:
            return _bcrypt.checkpw(
                plaintext.encode('utf-8'),
                self.api_key_hash.encode('utf-8'),
            )
        except (ValueError, TypeError):
            return False

    def __repr__(self):
        return f'<RVM {self.name} ({"Online" if self.is_online else "Offline"})>'


class RecyclingSession(db.Model):
    """
    Opened when a user scans their QR on the machine.
    Groups multiple RecyclingItems into one visit.
    """
    __tablename__ = 'recycling_sessions'
    id = db.Column(db.Integer, primary_key=True)
    rvm_id = db.Column(db.Integer, db.ForeignKey('rvms.id'), nullable=False, index=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False, index=True)
    total_points_earned = db.Column(db.Integer, default=0)
    item_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')           # active, completed, timed_out, error
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime, nullable=True)
    # Phase 3 task 8.2: free-form notes attached to a session (mainly used
    # by the bulk-deposit admin modal). Migration: phase3_session_notes.
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    items = db.relationship('RecyclingItem', backref='session', lazy=True,
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<RecyclingSession {self.id} ({self.status})>'


class RecyclingItem(db.Model):
    """
    A single item deposited during a session.
    Uses ML-detected classification (YOLOv8 output).
    """
    __tablename__ = 'recycling_items'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('recycling_sessions.id'),
                           nullable=False, index=True)
    detected_class = db.Column(db.String(200), nullable=False)    # YOLOv8 output
    points_awarded = db.Column(db.Integer, default=0)
    confidence_score = db.Column(db.Numeric(5, 2), nullable=True) # e.g. 95.50
    status = db.Column(db.String(20), default='Accepted')         # Accepted, Rejected
    scanned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<RecyclingItem {self.detected_class} | {self.points_awarded} pts>'


class MaintenanceLog(db.Model):
    """
    Logs maintenance/repair actions on RVMs.
    """
    __tablename__ = 'maintenance_logs'
    id = db.Column(db.Integer, primary_key=True)
    rvm_id = db.Column(db.Integer, db.ForeignKey('rvms.id'), nullable=False, index=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                                nullable=False, index=True)
    action_type = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pending')          # Resolved, Pending, Cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<MaintenanceLog {self.action_type} ({self.status})>'


# ============================================================================
# Group 3: Economy (Points & Rewards)
# ============================================================================

class Transaction(db.Model):
    """
    Ledger for all point movements.
    Records balance_before and balance_after for audit trail.
    """
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(50), nullable=False)   # earn, redeem, bulk_transaction
    amount = db.Column(db.Integer, nullable=False)                # + for earn, - for redeem
    balance_before = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50), nullable=True)      # session, redemption, admin_log, bulk_deposit
    reference_id = db.Column(db.Integer, nullable=True)           # FK to specific event
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.amount:+d} pts>'


class RewardCategory(db.Model):
    """
    CRUD-managed reward categories per organization.
    Replaces the previous plain-string category on Reward.
    """
    __tablename__ = 'reward_categories'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    rewards = db.relationship('Reward', backref='category_ref', lazy=True)

    def __repr__(self):
        return f'<RewardCategory {self.name}>'


class Reward(db.Model):
    """
    A redeemable item offered by a specific Organization.
    Stock is tracked per-variant in REWARD_VARIANTS.
    """
    __tablename__ = 'rewards'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))                          # Legacy string — kept for migration
    category_id = db.Column(db.Integer, db.ForeignKey('reward_categories.id'),
                            nullable=True, index=True)            # New FK to RewardCategory
    points_required = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)        # When reward was disabled
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    variants = db.relationship('RewardVariant', backref='reward', lazy=True,
                               cascade='all, delete-orphan')
    org_assignments = db.relationship('RewardOrgAssignment', backref='reward',
                                     lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Reward {self.name} ({self.points_required} pts)>'


class RewardOrgAssignment(db.Model):
    """Many-to-many: a reward can be visible to multiple organizations.

    The owning organization is still ``Reward.organization_id``. This table
    records *additional* organizations that should see the reward (shared
    merchandise). Superadmin-only — Task 29.
    """
    __tablename__ = 'reward_organization_assignments'
    __table_args__ = (
        db.UniqueConstraint('reward_id', 'organization_id',
                            name='uq_reward_org'),
    )
    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey('rewards.id'),
                          nullable=False, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    assigned_at = db.Column(db.DateTime,
                            default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<RewardOrgAssignment reward={self.reward_id} org={self.organization_id}>'


class RewardVariant(db.Model):
    """
    A specific variant/SKU of a reward (e.g. Red - Medium, Blue - Large).
    Stock is tracked at the variant level.
    """
    __tablename__ = 'reward_variants'
    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey('rewards.id'), nullable=False, index=True)
    variety_name = db.Column(db.String(200), nullable=False)      # e.g. "Red - Medium"
    stock_quantity = db.Column(db.Integer, default=0)
    points_required = db.Column(db.Integer, nullable=True)        # NULL = inherit parent Reward.points_required
    image_url = db.Column(db.String(500), nullable=True)          # Variant-specific product image
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    redemptions = db.relationship('RewardRedemption', backref='variant', lazy=True)

    def __repr__(self):
        return f'<RewardVariant {self.variety_name} (stock={self.stock_quantity})>'


class RewardRedemption(db.Model):
    """
    A digital voucher created when a user redeems points for a reward variant.
    """
    __tablename__ = 'reward_redemptions'
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('reward_variants.id'),
                           nullable=False, index=True)
    points_spent = db.Column(db.Integer, nullable=False)          # Locked snapshot of cost
    status = db.Column(db.String(20), default='pending')          # pending, claimed
    redemption_code = db.Column(db.String(50), unique=True, nullable=False)
    redeemed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    claimed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<RewardRedemption {self.redemption_code} ({self.status})>'


class BulkDeposit(db.Model):
    """
    Admin-initiated manual point deposit for users who bring
    recyclables that can't go through the RVM (e.g. bags of bottles).
    """
    __tablename__ = 'bulk_deposits'
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                              nullable=False, index=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False, index=True)
    total_points_awarded = db.Column(db.Integer, nullable=False)
    item_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<BulkDeposit {self.total_points_awarded} pts>'


# ============================================================================
# Group 4: Audit Trail
# ============================================================================

class AdminLog(db.Model):
    """
    Tracks all admin actions for accountability.
    """
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                              nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(200))
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f'<AdminLog {self.action} by User {self.admin_user_id}>'


# ============================================================================
# Group 5: Notifications & Alerts
# ============================================================================

class NotificationSetting(db.Model):
    """
    Per-organization notification configuration.
    """
    __tablename__ = 'notification_settings'
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'alert_key', name='uq_org_alert_key'),
    )
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    alert_key = db.Column(db.String(50), nullable=False)
    threshold = db.Column(db.Integer, nullable=True)
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    recipients_json = db.Column(db.Text, default='[]')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<NotificationSetting {self.alert_key} org={self.organization_id}>'


class NotificationLog(db.Model):
    """
    Audit trail for every notification sent (or attempted).
    """
    __tablename__ = 'notification_logs'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'),
                                nullable=False, index=True)
    alert_key = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(10), nullable=False)            # email, sms
    recipient = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(300))
    body_preview = db.Column(db.String(500))
    status = db.Column(db.String(20), default='sent')             # sent, failed
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<NotificationLog {self.alert_key} → {self.recipient} ({self.status})>'


# ============================================================================
# Group 6: Token Management & Security
# ============================================================================

class TokenBlacklist(db.Model):
    """
    Stores invalidated JWT tokens (on logout).
    """
    __tablename__ = 'token_blacklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'


class LoginAttempt(db.Model):
    """Tracks login attempts for security monitoring and account lockout."""
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(200), nullable=False, index=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    is_success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<LoginAttempt {self.identifier} ({"OK" if self.is_success else "FAIL"})>'