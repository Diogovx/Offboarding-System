# app/modules/offboarding/use_cases/disable_ad_account.py

import logging
from fastapi import Request
from fastapi.concurrency import run_in_threadpool

from app.integrations.active_directory import ADService, DisableUserRequest
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def disable_ad_account(
    *,
    registration: str,
    current_user,
    target_username: str,
    ad_service: ADService,
    session,
    req: Request,
) -> bool:
    """Disables the user account in Active Directory and logs the audit result.

    Args:
        registration (str): Employee registration number used as AD identifier.
        current_user: Authenticated user performing the offboarding.
        target_username (str): Display name of the user being offboarded.
        ad_service (ADService): Active Directory service instance.
        session: Active SQLAlchemy database session.
        req (Request): FastAPI request object for IP and user-agent extraction.

    Returns:
        bool: True if the account was disabled or was already disabled, False on failure.
    """
    try:
        payload = DisableUserRequest(
            registration=registration,
            performed_by=current_user.username,
        )
        result = await run_in_threadpool(ad_service.disable_user, payload)

        if result.action in ("disabled", "already_disabled"):
            if result.action == "already_disabled":
                logger.warning(
                    f"AD state mismatch for {registration}: "
                    "reported active but found already disabled."
                )
            else:
                create_audit_log(
                    session,
                    AuditLogCreate(
                        action=AuditAction.DISABLE_AD_USER,
                        status=AuditStatus.SUCCESS,
                        message=f"Network: User {registration} deactivated from AD.",
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
        logger.error(f"AD error for {registration}: {e}")
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.FAILED,
                message=f"AD deactivation failed: {e}",
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
