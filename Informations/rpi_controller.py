"""
RPI Controller (Phase 4A — hardened)
Handles all API endpoints for the Raspberry Pi (RVM hardware).

Phase 4A changes:
  - Every route is guarded by ``@rpi_auth_required`` which validates the
    ``X-API-Key`` header against the RVM's BCrypt-hashed API key.
  - Every POST handler has ``@validate_request(Schema)`` for strict input.
  - ``POST /api/rpi/authenticate`` validates the HMAC suffix on the QR
    payload BEFORE any User.query call (Requirement 4A.5, 4A.6).
"""
import hmac as _hmac
from datetime import datetime, timezone
from flask import Blueprint, jsonify

from ..models import (
    User, RecyclingSession, RecyclingItem, Transaction, Wallet, MaintenanceLog,
)
from ..middleware import rpi_auth_required, compute_qr_suffix, validate_request
from ..schemas import (
    RpiMachineIdentifySchema, RpiHeartbeatSchema, RpiAuthenticateSchema,
    RpiSessionStartSchema, RpiDepositSchema, RpiSessionEndSchema,
    RpiMachineStatusSchema, RpiMachineLogCreateSchema,
)
from .. import db
from ..cache import cache_invalidate

rpi_bp = Blueprint('rpi', __name__, url_prefix='/api/rpi')


# ══════════════════════════════════════════════════════════════════════════
# MACHINE AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════

@rpi_bp.route('/machine/identify', methods=['POST'])
@rpi_auth_required
@validate_request(RpiMachineIdentifySchema)
def identify_machine(rvm, payload):
    """Identify and authenticate an RVM by its machine_uuid.

    The RVM is already resolved and authenticated by ``@rpi_auth_required``.
    """
    try:
        return jsonify({
            'success': True,
            'machine': {
                'id': rvm.id,
                'name': rvm.name,
                'locationName': rvm.location_name,
                'isOnline': rvm.is_online,
                'isCapacityFull': rvm.is_capacity_full,
                'organizationId': rvm.organization_id,
            }
        }), 200
    except Exception:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@rpi_bp.route('/machine/heartbeat', methods=['POST'])
@rpi_auth_required
@validate_request(RpiHeartbeatSchema)
def machine_heartbeat(rvm, payload):
    """Periodic heartbeat from an RVM to confirm it's alive."""
    try:
        rvm.is_online = True
        if payload.isCapacityFull is not None:
            rvm.is_capacity_full = payload.isCapacityFull
        db.session.commit()

        return jsonify({'success': True, 'message': 'Heartbeat received'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


# ══════════════════════════════════════════════════════════════════════════
# USER AUTHENTICATION (QR Code + HMAC validation)
# ══════════════════════════════════════════════════════════════════════════

@rpi_bp.route('/authenticate', methods=['POST'])
@rpi_auth_required
@validate_request(RpiAuthenticateSchema)
def authenticate_user(rvm, payload):
    """Authenticate a user via HMAC-signed QR code payload.

    Phase 4A HMAC validation (Requirement 4A.5, 4A.6):
      1. Split ``qrPayload`` on the rightmost ``.`` into
         ``display_id`` and ``hmac_suffix``.
      2. Compute ``HMAC-SHA256(per_org_secret, display_id)[:6]``.
      3. Constant-time compare via ``hmac.compare_digest``.
      4. On mismatch → 401 ``QR_HMAC_INVALID`` (NO user DB lookup).
      5. On match → resolve user by ``display_id``.
    """
    try:
        qr_payload = payload.qrPayload
        print(f"[DEBUG AUTH] qr_payload: {qr_payload!r}")

        # Split on rightmost '.' to extract HMAC suffix
        if '.' not in qr_payload:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QR_HMAC_INVALID',
                    'message': 'QR payload must contain HMAC suffix',
                },
            }), 401

        last_dot = qr_payload.rfind('.')
        display_id = qr_payload[:last_dot]
        hmac_suffix = qr_payload[last_dot + 1:]
        print(f"[DEBUG AUTH] parsed display_id: {display_id!r}, hmac_suffix: {hmac_suffix!r}")

        if not display_id or not hmac_suffix:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QR_HMAC_INVALID',
                    'message': 'Invalid QR payload format',
                },
            }), 401

        # Get per-org HMAC secret
        try:
            org_secret = rvm.organization.get_qr_hmac_secret()
        except (ValueError, AttributeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QR_HMAC_INVALID',
                    'message': 'Organization HMAC secret not provisioned',
                },
            }), 401

        # Constant-time HMAC comparison — BEFORE any User.query
        expected_suffix = compute_qr_suffix(org_secret, display_id)
        if not _hmac.compare_digest(hmac_suffix.lower(), expected_suffix.lower()):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QR_HMAC_INVALID',
                    'message': 'QR code HMAC verification failed',
                },
            }), 401

        # HMAC valid — now look up the user
        user = User.query.filter_by(display_id=display_id, is_active=True).first()
        if not user:
            return jsonify({'success': False, 'error': 'Invalid QR code or user not found'}), 404

        wallet = user.wallet
        if not wallet:
            return jsonify({'success': False, 'error': 'User has no wallet'}), 404

        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'displayId': user.display_id,
                'pointsBalance': wallet.points_balance,
                'streak': wallet.streak,
                'role': user.role,
            },
            'walletId': wallet.id,
        }), 200
    except Exception:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


# ══════════════════════════════════════════════════════════════════════════
# RECYCLING SESSIONS
# ══════════════════════════════════════════════════════════════════════════

@rpi_bp.route('/session/start', methods=['POST'])
@rpi_auth_required
@validate_request(RpiSessionStartSchema)
def start_session(rvm, payload):
    """Start a new recycling session."""
    try:
        wallet_id = payload.walletId

        wallet = db.session.get(Wallet, wallet_id)
        if not wallet:
            return jsonify({'success': False, 'error': 'Wallet not found'}), 404

        if rvm.is_capacity_full:
            return jsonify({'success': False, 'error': 'Machine is full — cannot accept items'}), 400

        session = RecyclingSession(
            rvm_id=rvm.id,
            wallet_id=wallet_id,
            status='active',
            total_points_earned=0,
            item_count=0,
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'rvmId': rvm.id,
                'walletId': wallet_id,
                'status': session.status,
                'startTime': session.start_time.isoformat() if session.start_time else None,
            }
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@rpi_bp.route('/session/<int:session_id>/deposit', methods=['POST'])
@rpi_auth_required
@validate_request(RpiDepositSchema)
def deposit_item(rvm, session_id, payload):
    """Deposit a single item during an active session."""
    try:
        session = db.session.get(RecyclingSession, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        if session.status != 'active':
            return jsonify({'success': False, 'error': 'Session is not active'}), 400

        detected_class = payload.detectedClass or 'Unknown'
        confidence = payload.confidenceScore
        points = int(payload.pointsAwarded or 0)
        status = payload.status or 'Accepted'

        if status not in ('Accepted', 'Rejected'):
            return jsonify({'success': False, 'error': 'Status must be "Accepted" or "Rejected"'}), 400

        # If rejected, no points
        if status == 'Rejected':
            points = 0

        item = RecyclingItem(
            session_id=session_id,
            detected_class=detected_class,
            confidence_score=confidence,
            points_awarded=points,
            status=status,
        )
        db.session.add(item)

        session.item_count = (session.item_count or 0) + 1
        session.total_points_earned = (session.total_points_earned or 0) + points
        db.session.commit()

        # Bust dashboard cache since bottle counts changed
        cache_invalidate('dashboard_stats')

        return jsonify({
            'success': True,
            'item': {
                'id': item.id,
                'detectedClass': item.detected_class,
                'confidenceScore': float(item.confidence_score) if item.confidence_score else None,
                'pointsAwarded': item.points_awarded,
                'status': item.status,
            },
            'sessionTotals': {
                'itemCount': session.item_count,
                'totalPointsEarned': session.total_points_earned,
            }
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@rpi_bp.route('/session/<int:session_id>/end', methods=['POST'])
@rpi_auth_required
@validate_request(RpiSessionEndSchema)
def end_session(rvm, session_id, payload):
    """End an active session and credit points to the wallet."""
    try:
        session = db.session.get(RecyclingSession, session_id)
        if not session:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        if session.status != 'active':
            return jsonify({'success': False, 'error': 'Session is not active'}), 400

        final_status = payload.status or 'completed'
        if final_status not in ('completed', 'timed_out', 'error'):
            return jsonify({'success': False, 'error': 'Invalid status'}), 400

        session.status = final_status
        session.end_time = datetime.now(timezone.utc)

        total_points = session.total_points_earned or 0

        # Credit wallet only on successful completion
        if final_status == 'completed' and total_points > 0:
            wallet = db.session.get(Wallet, session.wallet_id)
            if wallet:
                balance_before = wallet.points_balance
                wallet.points_balance += total_points
                wallet.lifetime_points = (wallet.lifetime_points or 0) + total_points

                # Keep best_streak in sync whenever streak is tracked
                if (wallet.streak or 0) > (wallet.best_streak or 0):
                    wallet.best_streak = wallet.streak

                txn = Transaction(
                    wallet_id=wallet.id,
                    transaction_type='earn',
                    amount=total_points,
                    balance_before=balance_before,
                    balance_after=wallet.points_balance,
                    reference_type='session',
                    reference_id=session.id,
                )
                db.session.add(txn)

        db.session.commit()

        # Bust all data caches — points, leaderboard, and stats all changed
        cache_invalidate('dashboard_stats')
        cache_invalidate('leaderboard')
        cache_invalidate('analytics')

        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'status': session.status,
                'itemCount': session.item_count,
                'totalPointsEarned': session.total_points_earned,
                'startTime': session.start_time.isoformat() if session.start_time else None,
                'endTime': session.end_time.isoformat() if session.end_time else None,
            }
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@rpi_bp.route('/machine/status', methods=['POST'])
@rpi_auth_required
@validate_request(RpiMachineStatusSchema)
def update_machine_status(rvm, payload):
    """Update machine operational status."""
    try:
        if payload.isOnline is not None:
            rvm.is_online = payload.isOnline
        if payload.isCapacityFull is not None:
            rvm.is_capacity_full = payload.isCapacityFull

        db.session.commit()

        # ── Notification hooks ──
        try:
            from ..services.notification_service import trigger_alert
            if payload.isOnline is not None and not payload.isOnline:
                trigger_alert(rvm.organization_id, 'machine_offline',
                              f'Machine offline: {rvm.name}',
                              f'The machine "{rvm.name}" has gone offline.')
            if payload.isCapacityFull is not None and payload.isCapacityFull:
                trigger_alert(rvm.organization_id, 'machine_capacity_high',
                              f'Machine full: {rvm.name}',
                              f'Machine "{rvm.name}" reports its bin is full.')
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Machine status updated'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@rpi_bp.route('/logs/machines', methods=['POST'])
@rpi_auth_required
@validate_request(RpiMachineLogCreateSchema)
def create_machine_log(rvm, payload):
    """Create a new maintenance log entry from the RVM."""
    try:
        log = MaintenanceLog(
            rvm_id=rvm.id,
            performed_by_id=payload.performedById,
            action_type=payload.actionType,
            status=payload.status or 'Pending',
            notes=payload.notes or '',
        )
        db.session.add(log)
        db.session.commit()

        # Notification hook
        try:
            from ..services.notification_service import trigger_alert
            trigger_alert(rvm.organization_id, 'machine_maintenance_due',
                          f'Maintenance logged: {rvm.name}',
                          f'A new maintenance issue has been reported for "{rvm.name}": {payload.actionType}')
        except Exception:
            pass

        return jsonify({'success': True}), 201
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


# ══════════════════════════════════════════════════════════════════════════
# POINTS CONFIGURATION (for RVM-side point calculation)
# ══════════════════════════════════════════════════════════════════════════

@rpi_bp.route('/config/points/<int:org_id>', methods=['GET'])
@rpi_auth_required
def get_points_config(rvm, org_id):
    """Return the fixed point-per-bottle configuration.

    Points are no longer configurable per-org — the values are fixed in
    ``server/app/constants.py::BOTTLE_POINTS``.
    """
    from ..constants import BOTTLE_POINTS
    return jsonify({'success': True, 'config': BOTTLE_POINTS}), 200
