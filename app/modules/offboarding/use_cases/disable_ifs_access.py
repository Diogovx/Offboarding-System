import asyncio
import logging
import httpx
from fastapi import Request

from app.core.config import settings
from app.integrations.ifs.service import IFSService
from app.modules.audit.service import AuditLogCreate, create_audit_log
from app.modules.audit.enums import AuditAction, AuditStatus

logger = logging.getLogger(__name__)


async def check_ifs_status(registration: str) -> bool:
    """
    Checks IFS status in the Production environment.
    """
    try:
        ifs_service = IFSService(
            base_url=settings.IFS_BASE_URL,
            username=settings.IFS_USERNAME,
            password=settings.IFS_PASSWORD,
            client_id=settings.IFS_CLIENT_ID,
            client_secret=settings.IFS_CLIENT_SECRET
        )

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
    **kwargs
) -> bool:
    """
    Opens HTTP client and orchestrates deactivation in IFS (PRD and TST concurrently).
    """
    try:
        # (PRD) 
        ifs_prd = IFSService(
            base_url=settings.IFS_BASE_URL,
            username=settings.IFS_USERNAME,
            password=settings.IFS_PASSWORD,
            client_id=settings.IFS_CLIENT_ID,
            client_secret=settings.IFS_CLIENT_SECRET
        )

        # (TST)
        ifs_tst = IFSService(
            base_url=settings.IFS_TST_BASE_URL,
            username=settings.IFS_TST_USERNAME,
            password=settings.IFS_TST_PASSWORD,
            client_id=settings.IFS_TST_CLIENT_ID,
            client_secret=settings.IFS_TST_CLIENT_SECRET
        )

        async with httpx.AsyncClient() as client:
            
            task_prd = ifs_prd.disable_employee(registration, client)
            task_tst = ifs_tst.disable_employee(registration, client)
            
            result_prd, result_tst = await asyncio.gather(task_prd, task_tst, return_exceptions=True)

            is_prd_success = result_prd is True
            is_tst_success = result_tst is True

            overall_success = is_prd_success or is_tst_success

            log_message = (
                f"IFS Offboarding: "
                f"PRD=[{'Success' if is_prd_success else 'Failed/Not Found'}], "
                f"TST=[{'Success' if is_tst_success else 'Failed/Not Found'}]"
            )

            log_status = AuditStatus.SUCCESS if overall_success else AuditStatus.FAILED

            create_audit_log(
                session,
                AuditLogCreate(
                    action=AuditAction.DISABLE_IFS_USER,
                    status=log_status,
                    message=log_message,
                    user_id=current_user.id,
                    username=current_user.username,
                    target_username=target_username,
                    target_registration=registration,
                    resource=registration,
                    ip_address=req.client.host if req.client else None,
                    user_agent=req.headers.get("user-agent"),
                ),
            )

            return overall_success

    except Exception as e:
        logger.error(f"Critical orchestration error for IFS deactivation ({registration}): {e}")
        
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.DISABLE_IFS_USER,
                status=AuditStatus.FAILED,
                message=f"IFS deactivation failed: {str(e)}",
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