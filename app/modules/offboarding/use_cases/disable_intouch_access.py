# app/modules/offboarding/use_cases/deactivate_intouch.py

import logging
from fastapi import Request

from app.integrations.intouch import service as intouch_service
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def disable_intouch_access(
    *,
    registration: str,
    current_user,
    target_username: str,
    session,
    req: Request,
) -> bool:
    """Deactivates the user in the InTouch (Staffbase) platform and logs the result.

    Args:
        registration (str): Employee registration number used to identify the user.
        current_user: Authenticated user performing the offboarding.
        target_username (str): Display name of the user being offboarded.
        session: Active SQLAlchemy database session.
        req (Request): FastAPI request object for IP and user-agent extraction.

    Returns:
        bool: True if deactivation succeeded, False otherwise.
    """
    try:
        result = await intouch_service.deactivate_user_intouch(registration)

        status = AuditStatus.SUCCESS if result.success else AuditStatus.FAILED
        message = result.message if result.success else result.error

        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_INTOUCH_USER,
                status=status,
                message=f"InTouch: {message}",
                user_id=current_user.id,
                username=current_user.username,
                target_username=target_username,
                target_registration=registration,
                resource=registration,
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("user-agent"),
            ),
        )
        return result.success

    except Exception as e:
        logger.error(f"InTouch error for {registration}: {e}")
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_INTOUCH_USER,
                status=AuditStatus.FAILED,
                message=f"InTouch deactivation failed: {e}",
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
