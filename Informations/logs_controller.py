"""
Logs Controller (Phase 1 — Domain_Controller extracted from web_controller.py).

Owns paths under `/logs/*`. Registered as a sub-blueprint of `web_bp`
so the externally visible URL prefix `/api/web/logs/...` remains
byte-identical with the pre-Phase-1 routing surface.

Phase 1 is a pure restructuring: decorators on every moved route are
preserved byte-for-byte. The `@admin_required` → `@permission_required`
substitution is the work of Phase 2.
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload, selectinload

from ..models import (
    RecyclingItem, RecyclingSession, RVM, MaintenanceLog,
    AdminLog, User, CommunityGroup, Wallet,
    RewardRedemption, RewardVariant, Reward,
    Transaction, Organization, NotificationSetting,
)
from ..middleware import token_required, permission_required, get_user_org_id, validate_request
from ..schemas import MachineLogCreateSchema, RewardRedemptionUpdateSchema
from ..services.notification_service import trigger_alert
from .. import db
from ._shared import (
    _dt,
    _serialize_bottle_log,
    _serialize_machine_log,
    _serialize_admin_log,
    _serialize_reward_log,
    _scope_location_id,
    _log_action,
)


logs_bp = Blueprint('logs', __name__, url_prefix='/logs')


# ══════════════════════════════════════════════════════════════════════════
# LOGS (read-only)
# ══════════════════════════════════════════════════════════════════════════

@logs_bp.route('/bottles', methods=['GET'])
@token_required
@permission_required('logs', allow_non_admin=True)
def get_bottle_logs(current_user):
    """Recycling item logs, scoped by location."""
    try:
        loc_id = _scope_location_id(current_user)
        query = RecyclingItem.query.join(RecyclingSession).options(
            joinedload(RecyclingItem.session)
                .joinedload(RecyclingSession.rvm)
                .joinedload(RVM.organization),
            joinedload(RecyclingItem.session)
                .joinedload(RecyclingSession.wallet)
                .joinedload(Wallet.user),
        )
        if loc_id:
            query = query.join(RVM, RecyclingSession.rvm_id == RVM.id).filter(RVM.organization_id == loc_id)
            
        if not current_user.is_admin:
            wallet = current_user.wallet
            if wallet:
                query = query.filter(RecyclingSession.wallet_id == wallet.id)
            else:
                return jsonify({'success': True, 'logs': []}), 200
            
        items = query.order_by(RecyclingItem.scanned_at.desc()).limit(500).all()
        return jsonify({'success': True, 'logs': [_serialize_bottle_log(i) for i in items]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/machines', methods=['GET'])
@token_required
@permission_required('logs')
def get_machine_logs(current_user):
    """Maintenance logs, scoped by location."""
    try:
        loc_id = _scope_location_id(current_user)
        query = MaintenanceLog.query.join(RVM).options(
            joinedload(MaintenanceLog.rvm)
                .joinedload(RVM.organization),
            joinedload(MaintenanceLog.performed_by),
        )
        if loc_id:
            query = query.filter(RVM.organization_id == loc_id)
            
        if not current_user.is_admin:
            return jsonify({'success': True, 'logs': []}), 200
            
        logs = query.order_by(MaintenanceLog.created_at.desc()).limit(500).all()

        # ── Notification hook: maintenance_unresolved ──
        try:
            if loc_id:
                unresolved_setting = NotificationSetting.query.filter_by(
                    organization_id=loc_id,
                    alert_key='maintenance_unresolved', is_active=True
                ).first()
                if unresolved_setting:
                    threshold_hrs = (unresolved_setting.threshold or 48)
                    cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hrs)
                    unresolved = [l for l in logs if l.status == 'Pending' and l.created_at and l.created_at < cutoff]
                    for log_entry in unresolved[:5]:
                        rvm_name = log_entry.rvm.name if log_entry.rvm else f'RVM #{log_entry.rvm_id}'
                        trigger_alert(loc_id, 'maintenance_unresolved',
                                      f'Unresolved maintenance: {rvm_name}',
                                      f'Maintenance log "{log_entry.action_type}" on "{rvm_name}" '
                                      f'has been unresolved for over {threshold_hrs} hours.')
        except Exception:
            pass

        return jsonify({'success': True, 'logs': [_serialize_machine_log(l) for l in logs]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/machines', methods=['POST'])
@token_required
@permission_required('logs')
@validate_request(MachineLogCreateSchema)
def create_machine_log(current_user, payload):
    """Create a new maintenance log entry."""
    try:
        rvm_id = payload.rvmId
        action_type = payload.actionType

        if not rvm_id or not action_type:
            return jsonify({'success': False, 'error': 'rvmId and actionType are required'}), 400

        rvm = db.session.get(RVM, rvm_id)
        if not rvm:
            return jsonify({'success': False, 'error': 'Machine not found'}), 404

        if current_user.role != 'superadmin':
            if rvm.organization_id != _scope_location_id(current_user):
                return jsonify({'success': False, 'error': 'Access denied'}), 403

        log = MaintenanceLog(
            rvm_id=rvm_id,
            performed_by_id=current_user.id,
            action_type=action_type,
            status=payload.status or 'Pending',
            notes=payload.notes or '',
        )
        db.session.add(log)
        _log_action(current_user, 'Maintenance Log Created',
                     f'{action_type} on {rvm.name}', 'Machines')
        db.session.commit()

        # ── Notification hook: maintenance log created ──
        try:
            trigger_alert(rvm.organization_id, 'machine_maintenance_due',
                          f'Maintenance logged: {rvm.name}',
                          f'A new maintenance issue has been reported for "{rvm.name}": {action_type}')
        except Exception:
            pass

        return jsonify({'success': True, 'log': _serialize_machine_log(log)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/access', methods=['GET'])
@token_required
@permission_required('logs')
def get_access_logs(current_user):
    """Admin action logs, scoped by location."""
    try:
        loc_id = _scope_location_id(current_user)
        query = AdminLog.query.join(User, AdminLog.admin_user_id == User.id).options(
            selectinload(AdminLog.admin)
                .selectinload(User.community_group)
                .selectinload(CommunityGroup.organization),
        )
        if loc_id:
            query = query.join(CommunityGroup, User.community_group_id == CommunityGroup.id)\
                         .filter(CommunityGroup.organization_id == loc_id)\
                         .filter(User.role != 'superadmin')
                         
        if not current_user.is_admin:
            return jsonify({'success': True, 'logs': []}), 200
            
        logs = query.order_by(AdminLog.created_at.desc()).limit(500).all()
        return jsonify({'success': True, 'logs': [_serialize_admin_log(l) for l in logs]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/rewards', methods=['GET'])
@token_required
@permission_required('logs')
def get_reward_logs(current_user):
    """Reward redemption logs, scoped by location."""
    try:
        loc_id = _scope_location_id(current_user)
        query = RewardRedemption.query.join(RewardVariant).join(Reward).options(
            joinedload(RewardRedemption.wallet)
                .joinedload(Wallet.user),
            joinedload(RewardRedemption.variant)
                .joinedload(RewardVariant.reward)
                .joinedload(Reward.organization),
        )
        if loc_id:
            query = query.filter(Reward.organization_id == loc_id)
            
        if not current_user.is_admin:
            wallet = current_user.wallet
            if wallet:
                query = query.filter(RewardRedemption.wallet_id == wallet.id)
            else:
                return jsonify({'success': True, 'logs': []}), 200
            
        logs = query.order_by(RewardRedemption.redeemed_at.desc()).limit(500).all()
        return jsonify({'success': True, 'logs': [_serialize_reward_log(r) for r in logs]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/rewards/<int:redemption_id>', methods=['PUT'])
@token_required
@permission_required('logs')
@validate_request(RewardRedemptionUpdateSchema)
def update_reward_redemption(current_user, redemption_id, payload):
    """Update a reward redemption status (pending→claimed)."""
    try:
        rd = db.session.get(RewardRedemption, redemption_id)
        if not rd:
            return jsonify({'success': False, 'error': 'Redemption not found'}), 404

        # ── Org scope check via variant → reward ──
        variant = rd.variant
        reward = variant.reward if variant else None
        if current_user.role != 'superadmin' and reward:
            if reward.organization_id != get_user_org_id(current_user):
                return jsonify({'success': False, 'error': 'Access denied'}), 403

        new_status = payload.status
        valid_statuses = ('pending', 'claimed')
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': f'Invalid status. Must be one of {valid_statuses}'}), 400

        old_status = rd.status
        rd.status = new_status
        if new_status == 'claimed' and not rd.claimed_at:
            rd.claimed_at = datetime.now(timezone.utc)
            if old_status == 'pending':
                wallet = rd.wallet
                if wallet:
                    confirm_txn = Transaction(
                        wallet_id=rd.wallet_id,
                        transaction_type='redeem_confirm',
                        amount=0,
                        balance_before=wallet.points_balance,
                        balance_after=wallet.points_balance,
                        reference_type='reward_redemption',
                        reference_id=rd.id,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(confirm_txn)

        _log_action(current_user, 'Redemption Status Updated',
                     f'{rd.redemption_code}: {old_status} → {new_status}', 'Rewards')
        db.session.commit()

        # ── Notification hook: new redemption ──
        try:
            if new_status == 'claimed' and old_status == 'pending':
                reward_name = reward.name if reward else 'Unknown'
                org_id = reward.organization_id if reward else None
                if org_id:
                    trigger_alert(org_id, 'new_redemption',
                                  f'Reward redeemed: {reward_name}',
                                  f'Redemption {rd.redemption_code} for "{reward_name}" was claimed.')
        except Exception:
            pass

        return jsonify({'success': True, 'log': _serialize_reward_log(rd)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


@logs_bp.route('/transactions', methods=['GET'])
@token_required
@permission_required('logs', allow_non_admin=True)
def get_transaction_logs(current_user):
    """Transaction logs (earn/redeem/adjustment), scoped by location."""
    try:
        loc_id = _scope_location_id(current_user)
        query = db.session.query(Transaction, Wallet, User).join(
            Wallet, Transaction.wallet_id == Wallet.id
        ).join(
            User, Wallet.user_id == User.id
        ).join(
            CommunityGroup, User.community_group_id == CommunityGroup.id
        ).join(
            Organization, CommunityGroup.organization_id == Organization.id
        )
        if loc_id:
            query = query.filter(Organization.id == loc_id)
            
        if not current_user.is_admin:
            wallet = current_user.wallet
            if wallet:
                query = query.filter(Transaction.wallet_id == wallet.id)
            else:
                return jsonify({'success': True, 'logs': []}), 200
            
        rows = query.order_by(Transaction.created_at.desc()).limit(500).all()
        result = []
        for txn, w, user in rows:
            org_name = None
            if user.community_group and user.community_group.organization:
                org_name = user.community_group.organization.name
            result.append({
                'id': txn.id,
                'walletId': txn.wallet_id,
                'userName': user.name,
                'userEmail': user.email,
                'transactionType': txn.transaction_type,
                'amount': txn.amount,
                'balanceBefore': txn.balance_before,
                'balanceAfter': txn.balance_after,
                'referenceType': txn.reference_type,
                'referenceId': txn.reference_id,
                # Phase 3 task 8.2 (alignment-doc §9): derive a human-
                # readable description from the (transaction_type,
                # reference_type, reference_id) triple. There is no
                # `description` column on `transactions`, so we compute
                # one on the way out. Returns `None` when nothing
                # meaningful can be derived.
                'description': _describe_transaction(txn),
                'locationId': user.community_group.organization_id if user.community_group else None,
                'locationName': org_name,
                'timestamp': _dt(txn.created_at),
            })
        return jsonify({'success': True, 'logs': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500


def _describe_transaction(txn):
    """Derive a human-readable description for a `Transaction` row.

    The model has no `description` column today (alignment-doc §9). We
    fold `(transaction_type, reference_type, reference_id)` into a short
    human label so the logs/transactions page can drop its `|| '—'`
    fallback. Returns `None` when nothing meaningful can be computed
    (the page renders the empty-state in that case).
    """
    txn_type = (txn.transaction_type or '').lower() or None
    ref_type = (txn.reference_type or '').lower() or None
    ref_id = txn.reference_id

    # Most informative combinations first.
    if ref_type == 'reward_redemption' and ref_id is not None:
        rd = db.session.get(RewardRedemption, ref_id)
        if rd and rd.variant and rd.variant.reward:
            reward_name = rd.variant.reward.name
            if txn_type == 'redeem_confirm':
                return f'Claimed Reward: {reward_name}'
            return f'Redeemed Reward: {reward_name}'
        if txn_type == 'redeem_confirm':
            return f'Claimed Reward #{ref_id}'
        return f'Reward redemption #{ref_id}'
    if ref_type == 'recycling_session' and ref_id is not None:
        return f'Bottle deposit (session #{ref_id})'
    if ref_type == 'bulk_deposit' and ref_id is not None:
        return f'Bulk deposit #{ref_id}'
    if txn_type == 'adjustment':
        return 'Manual adjustment'
    if txn_type == 'earn':
        return 'Points earned'
    if txn_type == 'redeem':
        return 'Points redeemed'
    if txn_type == 'bulk_transaction':
        return 'Bulk points credit'
    return None
