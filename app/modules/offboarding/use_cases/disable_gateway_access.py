# app/modules/offboarding/use_cases/revoke_gate_access.py

import logging
from fastapi import Request

from app.integrations.gate import deactivate_user_turnstiles
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def disable_gateway_access(
    *,
    registration: str,
    current_user,
    target_username: str,
    session,
    req: Request,
) -> bool:
    """Revokes user access in all gate turnstiles and logs the audit result.

    Args:
        registration (str): Employee registration number.
        current_user: Authenticated user performing the offboarding.
        target_username (str): Display name of the user being offboarded.
        session: Active SQLAlchemy database session.
        req (Request): FastAPI request object for IP and user-agent extraction.

    Returns:
        bool: True if access was revoked successfully, False otherwise.
    """
    try:
        result = await deactivate_user_turnstiles(registration=registration)

        if result.get("success"):
            create_audit_log(
                session,
                AuditLogCreate(
                    action=AuditAction.DISABLE_TURNSTILE_USER,
                    status=AuditStatus.SUCCESS,
                    message=f"Gateway: User {registration} blocked in all turnstiles.",
                    user_id=current_user.id,
                    username=current_user.username,
                    target_username=target_username,
                    target_registration=registration,
                    resource=registration,
                    ip_address=req.client.host if req.client else None,
                    user_agent=req.headers.get("user-agent"),
                ),
            )
            return True

    except Exception as e:
        logger.error(f"Gate error for {registration}: {e}")
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_TURNSTILE_USER,
                status=AuditStatus.FAILED,
                message=f"Gateway deactivation failed: {e}",
                user_id=current_user.id,
                username=current_user.username,
                target_username=target_username,
                target_registration=registration,
                resource=registration,
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("user-agent"),
            ),
        )

    return False
