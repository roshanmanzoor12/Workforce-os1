from __future__ import annotations

from app.config import settings
from app.modules.auth.models import User


async def is_billing_exempt(db, user_id) -> bool:
    """Server-only UUID allowlist. Membership/RBAC are deliberately separate."""
    if str(user_id) not in {str(value) for value in settings.billing_unlimited_user_ids}:
        return False
    user = await db.get(User, user_id)
    return bool(user is not None and user.is_active and user.is_email_verified and not user.is_locked)
