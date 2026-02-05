import json
from subprocess import PIPE, STDOUT, run

from fastapi import APIRouter, HTTPException, Request, status

from app.audit.audit_log_service import create_audit_log
from app.enums import AuditAction, AuditStatus
from app.models import ADUser, DisableUserRequest
from app.schemas import AuditLogCreate
from app.security import Current_user, Db_session

from app.services import search_aduser, ldap_entry_to_ad_user, disable_aduser

router = APIRouter(prefix="/aduser", tags=["ADUser"])


@router.get("/", response_model=list[ADUser])
async def get_user(
    session: Current_user,
    request: Request,
    db: Db_session,
    registration: str | None = None,
):
    try:
        entries = search_aduser(registration)

        if not entries:
            raise HTTPException(status_code=404, detail="User not found")

        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.SUCCESS,
                message="User research conducted",
                user_id=session.id,
                username=session.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

    except HTTPException:
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SEARCH_AD_USER,
                status=AuditStatus.FAILED,
                message="Error querying Active Directory.",
                user_id=session.id,
                username=session.username,
                resource=registration or "*",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
    return [ldap_entry_to_ad_user(e) for e in entries]


@router.post("/disable")
async def disable_user(
    payload: DisableUserRequest,
    session: Current_user,
    request: Request,
    db: Db_session
):
    disable_aduser(payload)

    create_audit_log(
        db,
        AuditLogCreate(
            action=AuditAction.DISABLE_AD_USER,
            status=AuditStatus.SUCCESS,
            message="User deactivated and moved successfully.",
            user_id=session.id,
            username=session.username,
            resource=payload.registration,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return {
        "status": "success",
        "user": payload.registration,
    }
