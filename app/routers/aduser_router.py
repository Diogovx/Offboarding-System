from logging import getLogger

from fastapi import APIRouter, HTTPException, Request, status

from app.audit.audit_log_service import create_audit_log
from app.database import Db_session
from app.enums import AuditAction, AuditStatus
from app.models import ADUser, DisableUserRequest
from app.schemas import AuditLogCreate
from app.security import Current_user
from app.services import ADServiceDep

logger = getLogger(__name__)

router = APIRouter(prefix="/aduser", tags=["ADUser"])


@router.get("/", response_model=list[ADUser])
async def get_user(
    ad_service: ADServiceDep,
    current_user: Current_user,
    request: Request,
    db: Db_session,
    registration: str | None = None,
):
    try:
        logger.info(
            f"User {current_user.username}"
            " searching AD - registration={registration}"
        )
        users = ad_service.search_users(registration=registration)

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.SUCCESS,
                message=f"User research conducted - {len(users)} founded",
                user_id=current_user.id,
                username=current_user.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

        logger.info(
            f"Found {len(users)} users for registration={registration}"
        )

        return users

    except HTTPException as e:
        logger.warning(f"HTTP error searching AD: {e.detail}")

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Search Failed: {e.detail}",
                user_id=current_user.id,
                username=current_user.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching AD: {e}", exc_info=True)

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Unexpected error: {str(e)}",
                user_id=current_user.id,
                username=current_user.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying Active Directory"
        )


@router.post("/disable")
async def disable_user(
    payload: DisableUserRequest,
    ad_service: ADServiceDep,
    current_user: Current_user,
    request: Request,
    db: Db_session
):
    try:
        logger.info(
            f"User {current_user.username} initiating AD user disable - "
            f"registration={payload.registration}, "
            "performed_by={payload.performed_by}"
        )
        user = ad_service.disable_user(payload)

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.SUCCESS,
                message=(
                    f"User '{user.sam_account_name}' ({user.name}) "
                    f"deactivated successfully by {payload.performed_by}"
                ),
                user_id=current_user.id,
                username=current_user.username,
                resource=payload.registration,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

        logger.info(f"User {user.sam_account_name} successfully disabled")

        return user

    except HTTPException as e:
        logger.warning(
            f"HTTP error disabling user {payload.registration}: "
            f"{e.status_code} - {e.detail}"
        )

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Failed to disable user: {e.detail}",
                user_id=current_user.id,
                username=current_user.username,
                resource=payload.registration,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise

    except Exception as e:
        logger.error(
            f"Unexpected error disabling user {payload.registration}: {e}",
            exc_info=True
        )

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_AD_USER,
                status=AuditStatus.FAILED,
                message=f"Failed to disable user: {type(e).__name__}",
                user_id=current_user.id,
                username=current_user.username,
                resource=payload.registration,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error disabling user in Active Directory"
        )
