"""
Server: input-validation layer (Phase 4E — task 14.1).

This module defines exactly one Pydantic v2 :class:`BaseModel` per request
body for every POST / PUT / PATCH handler in :mod:`auth_controller` and in
every Domain_Controller (``dashboard``, ``users``, ``locations``,
``machines``, ``rewards``, ``logs``, ``leaderboard``, ``groups``,
``analytics``, ``settings``, ``sessions``).

Phase 4A (resolved)
--------------------

RPI controller schemas are now authored below (``RpiIdentify``,
``RpiHeartbeat``, ``RpiAuthenticate``, ``RpiSessionStart``,
``RpiDeposit``, ``RpiSessionEnd``, ``RpiMachineStatus``). Each sets
``model_config = ConfigDict(extra='forbid', strict=True)`` per
Requirement 4E.23 / Property S.

Schema rules
------------

Every schema in this module sets::

    model_config = ConfigDict(extra='forbid', strict=True)

so that:

  * unknown keys produce a Pydantic ``extra_forbidden`` error (Requirement
    4E.25 / Property L — strict-acceptance), surfaced by the
    ``@validate_request`` decorator (task 14.2) as HTTP 400 ``UNKNOWN_FIELD``;
  * type mismatches (e.g., a string where an int was expected) produce a
    Pydantic ``int_type`` / ``string_type`` / ``bool_type`` error rather
    than being silently coerced — surfaced as HTTP 400 ``VALIDATION_ERROR``.

Field names match exactly what the existing handlers read off
``request.get_json()`` — no renaming. Fields the handler treats as optional
(``data.get('x')`` without a presence check, or ``if 'x' in data``) are
typed ``Optional[...]`` here.

Decorator wiring (tasks 14.2 / 14.3) is intentionally NOT done in this
module — this file is purely the schema catalogue.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────
# Strict base
# ──────────────────────────────────────────────────────────────────────────


class _StrictModel(BaseModel):
    """Base for every request schema in this module.

    Sets the two flags Requirement 4E.23 mandates for every mutating-route
    schema: ``extra='forbid'`` (reject unknown keys → ``UNKNOWN_FIELD``) and
    ``strict=True`` (reject silent type coercions → ``VALIDATION_ERROR``).
    """

    model_config = ConfigDict(extra='forbid', strict=True)


# ══════════════════════════════════════════════════════════════════════════
# auth_controller (auth_bp — prefix /api/web/auth)
# ══════════════════════════════════════════════════════════════════════════


class LoginSchema(_StrictModel):
    """Body for ``POST /api/web/auth/login``.

    Handler reads any of ``email`` / ``username`` / ``identifier`` for the
    login identifier and ``password`` for the secret. The "at least one of
    {email, username, identifier}" check stays in the handler so the
    schema's job is purely shape + types.
    """

    email: Optional[str] = None
    username: Optional[str] = None
    identifier: Optional[str] = None
    password: Optional[str] = None
    captchaToken: Optional[str] = None


class VerifyOtpSchema(_StrictModel):
    """Body for ``POST /api/web/auth/verify-otp``."""

    tempToken: Optional[str] = None
    code: Optional[str] = None


class LogoutSchema(_StrictModel):
    """Body for ``POST /api/web/auth/logout``.

    The handler does not read any body fields — the JWT is consumed from
    the ``Authorization`` header / cookie. We still register a schema so
    every mutating route is uniformly schema-validated (Property S).
    """


class ProfileUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/auth/profile``."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    # Backward-compat: handler accepts a single ``name`` and splits on
    # the first space when ``firstName`` is absent.
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    # Pass empty string or null to clear the avatar.
    avatar: Optional[str] = None


class ChangePasswordSchema(_StrictModel):
    """Body for ``POST /api/web/auth/change-password``."""

    currentPassword: Optional[str] = None
    newPassword: Optional[str] = None


class RegisterSchema(_StrictModel):
    """Body for ``POST /api/web/auth/register`` (public registration)."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    # Backward-compat: handler splits ``name`` when ``firstName`` is absent.
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    userType: Optional[Literal[
        'student', 'faculty', 'staff', 'alumni',
        'resident', 'community_official', 'community_worker', 'business_owner',
        'employee', 'manager', 'executive', 'contractor', 'guest',
    ]] = None
    yearLevel: Optional[str] = None
    locationId: Optional[int] = None
    groupId: Optional[int] = None


# ══════════════════════════════════════════════════════════════════════════
# users_controller (users_bp — prefix /api/web/users)
# ══════════════════════════════════════════════════════════════════════════


class UserCreateSchema(_StrictModel):
    """Body for ``POST /api/web/users``."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    # Backward-compat: handler splits ``name`` when ``firstName`` is absent.
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    userType: Optional[str] = None
    yearLevel: Optional[str] = None
    communityGroupId: Optional[int] = None
    isActive: Optional[bool] = None
    locationId: Optional[int] = None
    groupId: Optional[int] = None


class UserUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/users/<id>``."""

    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    # Backward-compat: handler splits ``name`` when ``firstName`` is absent.
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    userType: Optional[str] = None
    yearLevel: Optional[str] = None
    communityGroupId: Optional[int] = None
    isActive: Optional[bool] = None


class UserAdjustPointsSchema(_StrictModel):
    """Body for ``POST /api/web/users/<id>/adjust-points``.

    Handler accepts ``isinstance(amount, (int, float))`` then coerces via
    ``int(amount)``, so the schema accepts either type. ``bool`` is a
    subclass of ``int`` in Python, but ``strict=True`` makes Pydantic
    reject ``True``/``False`` for ``int`` fields, matching the handler's
    intent (a bool is not a valid point delta).
    """

    amount: Optional[Union[int, float]] = None
    reason: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════
# settings_controller (settings_bp — prefix /api/web/settings)
# ══════════════════════════════════════════════════════════════════════════


class NotificationSettingItem(_StrictModel):
    """One element inside ``NotificationSettingsUpdateSchema.settings``."""

    alertKey: Optional[str] = None
    emailEnabled: Optional[bool] = None
    smsEnabled: Optional[bool] = None
    threshold: Optional[int] = None
    # Recipients are persisted as JSON; handler does not constrain the
    # element type, so we accept any list.
    recipients: Optional[List[Any]] = None
    isActive: Optional[bool] = None


class NotificationSettingsUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/settings/notifications``."""

    settings: Optional[List[NotificationSettingItem]] = None


class NotificationTestSchema(_StrictModel):
    """Body for ``POST /api/web/settings/notifications/test``."""

    channel: Optional[Literal['email', 'sms']] = None
    recipient: Optional[str] = None


class PointsConfigUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/settings/points``."""

    extraSmallWithLabel: Optional[int] = None
    extraSmallNoLabel: Optional[int] = None
    smallWithLabel: Optional[int] = None
    smallNoLabel: Optional[int] = None
    mediumWithLabel: Optional[int] = None
    mediumNoLabel: Optional[int] = None
    largeWithLabel: Optional[int] = None
    largeNoLabel: Optional[int] = None


class ChannelConfigUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/settings/channels``."""

    emailRecipient: Optional[str] = None
    smsRecipient: Optional[str] = None
    emailEnabled: Optional[bool] = None
    smsEnabled: Optional[bool] = None


class SecurityConfigUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/settings/security``."""

    twoFactorRequired: Optional[bool] = None
    twoFactorMethod: Optional[Literal['email']] = None
    sessionTimeoutMinutes: Optional[int] = None
    maxLoginAttempts: Optional[int] = None
    lockoutDurationMinutes: Optional[int] = None


class ForceLogoutSchema(_StrictModel):
    """Body for ``POST /api/web/settings/security/force-logout``.

    Empty body schema: no fields are read by the handler. With
    ``extra='forbid'`` any non-empty body is rejected (Requirement 4C.18 /
    task 12.3 reference).
    """


class RestoreBackupMetaSchema(_StrictModel):
    """Metadata envelope inside ``RestoreBackupSchema.meta``."""

    version: Optional[str] = None
    created_at: Optional[str] = None
    table_count: Optional[int] = None


class RestoreBackupSchema(_StrictModel):
    """Body for ``POST /api/web/settings/restore``.

    The backup file is a JSON object with a ``meta`` envelope and a
    ``tables`` map.  Table values are arbitrary row arrays, so ``tables``
    is typed ``Optional[Any]`` to avoid enumerating every table name.
    The handler performs its own structural validation after parsing.
    """

    meta: Optional[RestoreBackupMetaSchema] = None
    tables: Optional[Any] = None


class SeedSchema(_StrictModel):
    """Body for ``POST /api/web/settings/seed``.

    ``mode`` controls whether demo data is generated (``'demo'``) or all
    tables are truncated (``'truncate'``).  Defaults to ``'demo'`` in the
    handler when omitted.
    """

    mode: Optional[Literal['demo', 'truncate']] = None


# ══════════════════════════════════════════════════════════════════════════
# sessions_controller (sessions_bp — owns /sessions/* and /bulk-deposits)
# ══════════════════════════════════════════════════════════════════════════


class BulkSessionItemSchema(_StrictModel):
    """One element inside ``BulkSessionCreateSchema.items``."""

    detectedClass: Optional[str] = None
    confidenceScore: Optional[float] = None
    pointsAwarded: Optional[int] = None
    status: Optional[str] = None


class BulkSessionCreateSchema(_StrictModel):
    """Body for ``POST /api/web/sessions/bulk``."""

    rvmId: Optional[int] = None
    walletId: Optional[int] = None
    items: Optional[List[BulkSessionItemSchema]] = None
    notes: Optional[str] = None


class BulkDepositCreateSchema(_StrictModel):
    """Body for ``POST /api/web/bulk-deposits``."""

    walletId: Optional[int] = None
    totalPointsAwarded: Optional[int] = None
    itemCount: Optional[int] = None
    notes: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════
# locations_controller (locations_bp — owns /locations/* and /org-types/*)
# ══════════════════════════════════════════════════════════════════════════


class OrgTypeCreateSchema(_StrictModel):
    """Body for ``POST /api/web/org-types``."""

    name: Optional[str] = None


class OrgTypeUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/org-types/<id>``."""

    name: Optional[str] = None


class CommunityGroupInlineSchema(_StrictModel):
    """One community group supplied inline during location creation."""

    name: str
    abbreviation: Optional[str] = None
    educationalLevel: Optional[str] = None


class LocationCreateSchema(_StrictModel):
    """Body for ``POST /api/web/locations``."""

    name: Optional[str] = None
    fullName: Optional[str] = None
    orgType: Optional[str] = None
    status: Optional[str] = None
    streetAddress: Optional[str] = None
    barangay: Optional[str] = None
    cityName: Optional[str] = None
    cityMunicipality: Optional[str] = None
    province: Optional[str] = None
    region: Optional[str] = None
    zipCode: Optional[str] = None
    contactPerson: Optional[str] = None
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None
    communityGroups: Optional[List[CommunityGroupInlineSchema]] = None


class CommunityGroupUpdateInlineSchema(_StrictModel):
    """One community group in a location update — may have an existing `id`."""

    id: Optional[int] = None
    name: str
    abbreviation: Optional[str] = None
    educationalLevel: Optional[str] = None


class LocationUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/locations/<id>``."""

    name: Optional[str] = None
    fullName: Optional[str] = None
    status: Optional[str] = None
    orgType: Optional[str] = None
    streetAddress: Optional[str] = None
    barangay: Optional[str] = None
    cityName: Optional[str] = None
    cityMunicipality: Optional[str] = None
    province: Optional[str] = None
    region: Optional[str] = None
    zipCode: Optional[str] = None
    contactPerson: Optional[str] = None
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None
    communityGroups: Optional[List[CommunityGroupUpdateInlineSchema]] = None


# ══════════════════════════════════════════════════════════════════════════
# machines_controller (machines_bp — prefix /api/web/machines)
# ══════════════════════════════════════════════════════════════════════════


class MachineCreateSchema(_StrictModel):
    """Body for ``POST /api/web/machines``."""

    locationId: Optional[int] = None
    machineUuid: Optional[str] = None
    name: Optional[str] = None
    locationName: Optional[str] = None
    isOnline: Optional[bool] = None


class MachineUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/machines/<id>``."""

    name: Optional[str] = None
    locationName: Optional[str] = None
    isOnline: Optional[bool] = None
    isCapacityFull: Optional[bool] = None


# ══════════════════════════════════════════════════════════════════════════
# rewards_controller (rewards_bp — prefix /api/web/rewards)
# ══════════════════════════════════════════════════════════════════════════


class RewardVariantInputSchema(_StrictModel):
    """One variant inside a reward create/update payload.

    ``pointsRequired = None`` means the variant inherits the parent reward's
    price. ``id`` is present only when editing an existing variant (upsert).
    """

    id: Optional[int] = None
    varietyName: Optional[str] = None
    stockQuantity: Optional[int] = None
    pointsRequired: Optional[int] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None


class RewardCreateSchema(_StrictModel):
    """Body for ``POST /api/web/rewards``."""

    locationId: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    categoryId: Optional[int] = None
    pointsRequired: Optional[int] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    stockQuantity: Optional[int] = None
    variants: Optional[List[RewardVariantInputSchema]] = None


class RewardUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/rewards/<id>``."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    categoryId: Optional[int] = None
    pointsRequired: Optional[int] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    stockQuantity: Optional[int] = None
    variants: Optional[List[RewardVariantInputSchema]] = None


class RewardCategoryCreateSchema(_StrictModel):
    """Body for ``POST /api/web/reward-categories``."""

    name: Optional[str] = None
    organizationId: Optional[int] = None


class RewardCategoryUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/reward-categories/<id>``."""

    name: Optional[str] = None


class RewardRedeemSchema(_StrictModel):
    """Body for ``POST /api/web/rewards/<id>/redeem``."""

    variantId: Optional[int] = None
    quantity: Optional[int] = Field(default=None)


class RewardAssignSchema(_StrictModel):
    """Body for ``POST /api/web/rewards/<id>/assign`` (Task 29).

    Superadmin assigns a reward to additional organizations so those
    organizations' users can also see and redeem the reward.
    """

    organizationIds: List[int]


# ══════════════════════════════════════════════════════════════════════════
# logs_controller (logs_bp — prefix /api/web/logs)
# ══════════════════════════════════════════════════════════════════════════


class MachineLogCreateSchema(_StrictModel):
    """Body for ``POST /api/web/logs/machines`` (maintenance log create)."""

    rvmId: Optional[int] = None
    actionType: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class RewardRedemptionUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/logs/rewards/<id>``.

    Handler validates ``status in ('pending', 'claimed')``; mirror that
    constraint here so an invalid value surfaces as a typed schema error
    rather than a free-form 400 from the handler.
    """

    status: Optional[Literal['pending', 'claimed']] = None


# ══════════════════════════════════════════════════════════════════════════
# groups_controller (groups_bp — prefix /api/web/groups)
# ══════════════════════════════════════════════════════════════════════════


class GroupCreateSchema(_StrictModel):
    """Body for ``POST /api/web/groups``."""

    name: Optional[str] = None
    abbreviation: Optional[str] = None
    educationalLevel: Optional[str] = None
    organizationId: Optional[int] = None


class GroupUpdateSchema(_StrictModel):
    """Body for ``PUT /api/web/groups/<id>``."""

    name: Optional[str] = None
    abbreviation: Optional[str] = None
    educationalLevel: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════
# rpi_controller (rpi_bp — prefix /api/rpi)  [Phase 4A]
# ══════════════════════════════════════════════════════════════════════════


class RpiMachineIdentifySchema(_StrictModel):
    """Body for ``POST /api/rpi/machine/identify``."""

    machineUuid: str


class RpiHeartbeatSchema(_StrictModel):
    """Body for ``POST /api/rpi/machine/heartbeat``."""

    machineUuid: str
    isCapacityFull: Optional[bool] = None


class RpiAuthenticateSchema(_StrictModel):
    """Body for ``POST /api/rpi/authenticate``.

    ``qrPayload`` format: ``<display_id>.<hmac_suffix>``
    """

    qrPayload: str
    machineUuid: str


class RpiSessionStartSchema(_StrictModel):
    """Body for ``POST /api/rpi/session/start``."""

    machineUuid: str
    walletId: int


class RpiDepositSchema(_StrictModel):
    """Body for ``POST /api/rpi/session/<id>/deposit``."""

    machineUuid: str
    detectedClass: Optional[str] = None
    confidenceScore: Optional[float] = None
    pointsAwarded: Optional[int] = None
    status: Optional[str] = None


class RpiSessionEndSchema(_StrictModel):
    """Body for ``POST /api/rpi/session/<id>/end``."""

    machineUuid: str
    status: Optional[str] = None


class RpiMachineStatusSchema(_StrictModel):
    """Body for ``POST /api/rpi/machine/status``."""

    machineUuid: str
    isOnline: Optional[bool] = None
    isCapacityFull: Optional[bool] = None


class RpiMachineLogCreateSchema(_StrictModel):
    """Body for ``POST /api/rpi/logs/machines``."""
    machineUuid: str
    actionType: str
    status: Optional[str] = 'Pending'
    notes: Optional[str] = ''
    performedById: int


class RotateApiKeySchema(_StrictModel):
    """Body for ``POST /api/web/machines/<id>/rotate-api-key``.

    Empty body: the server generates the key. ``extra='forbid'`` rejects
    any payload.
    """


# ──────────────────────────────────────────────────────────────────────────
# Password Reset (Forgot Password flow)
# ──────────────────────────────────────────────────────────────────────────

class ForgotPasswordSchema(_StrictModel):
    """Body for ``POST /api/web/auth/forgot-password``."""

    email: str


class VerifyResetOtpSchema(_StrictModel):
    """Body for ``POST /api/web/auth/verify-reset-otp``."""

    email: str
    code: str


class ResetPasswordSchema(_StrictModel):
    """Body for ``POST /api/web/auth/reset-password``."""

    resetToken: str
    newPassword: str


# ──────────────────────────────────────────────────────────────────────────
# Public re-exports
# ──────────────────────────────────────────────────────────────────────────

__all__ = [
    # auth_controller
    'LoginSchema',
    'VerifyOtpSchema',
    'LogoutSchema',
    'ProfileUpdateSchema',
    'ChangePasswordSchema',
    'RegisterSchema',
    # users_controller
    'UserCreateSchema',
    'UserUpdateSchema',
    'UserAdjustPointsSchema',
    # settings_controller
    'NotificationSettingItem',
    'NotificationSettingsUpdateSchema',
    'NotificationTestSchema',
    'PointsConfigUpdateSchema',
    'ChannelConfigUpdateSchema',
    'SecurityConfigUpdateSchema',
    'ForceLogoutSchema',
    'RestoreBackupMetaSchema',
    'RestoreBackupSchema',
    'SeedSchema',
    # sessions_controller
    'BulkSessionItemSchema',
    'BulkSessionCreateSchema',
    'BulkDepositCreateSchema',
    # locations_controller
    'OrgTypeCreateSchema',
    'OrgTypeUpdateSchema',
    'CommunityGroupInlineSchema',
    'LocationCreateSchema',
    'LocationUpdateSchema',
    # machines_controller
    'MachineCreateSchema',
    'MachineUpdateSchema',
    # rewards_controller
    'RewardVariantInputSchema',
    'RewardCreateSchema',
    'RewardUpdateSchema',
    'RewardRedeemSchema',
    'RewardAssignSchema',
    'RewardCategoryCreateSchema',
    'RewardCategoryUpdateSchema',
    # logs_controller
    'MachineLogCreateSchema',
    'RewardRedemptionUpdateSchema',
    # groups_controller
    'GroupCreateSchema',
    'GroupUpdateSchema',
    # rpi_controller (Phase 4A)
    'RpiMachineIdentifySchema',
    'RpiHeartbeatSchema',
    'RpiAuthenticateSchema',
    'RpiSessionStartSchema',
    'RpiDepositSchema',
    'RpiSessionEndSchema',
    'RpiMachineStatusSchema',
    'RpiMachineLogCreateSchema',
    'RotateApiKeySchema',
    # auth_controller — password reset
    'ForgotPasswordSchema',
    'VerifyResetOtpSchema',
    'ResetPasswordSchema',
]
