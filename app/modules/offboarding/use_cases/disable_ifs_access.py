from fastapi import Request
import httpx
import logging
from app.core.config import settings
from app.integrations.ifs.service import IFSService
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def check_ifs_status(registration: str) -> bool:
    """
    Checks IFS status.
    """
    try:

        ifs_service = IFSService(base_url=settings.IFS_BASE_URL)

        return await ifs_service.search_user(registration)

    except Exception as e:

        logger.error(
            f"Connection failed when checking IFS for {registration}: {e}"
        )
        return False


async def disable_ifs_access(
    registration: str,
    current_user,
    target_username: str,
    req: Request,
    session,
    **kwargs) -> bool:
    """
    Opens HTTP client and orchestrates deactivation in IFS
    """
    try:
        async with httpx.AsyncClient() as client:

            ifs_service = IFSService(base_url=settings.IFS_BASE_URL)
            create_audit_log(
                    session,
                    AuditLogCreate(
                        action=AuditAction.DISABLE_IFS_USER,
                        status=AuditStatus.SUCCESS,
                        message=f"IFS: User {registration} deactivated from IFS.",
                        user_id=current_user.id,
                        username=current_user.username,
                        target_username=target_username,
                        target_registration=registration,
                        resource=registration,
                        ip_address=req.client.host if req.client else None,
                        user_agent=req.headers.get("user-agent"),
                    ),
                )
            return await ifs_service.disable_employee(registration, client)

    except Exception as e:
        logger.error(f"Failed to deactivate user {registration} in IFS: {e}")
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_IFS_USER,
                status=AuditStatus.FAILED,
                message=f"IFS deactivation failed: {e}",
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
