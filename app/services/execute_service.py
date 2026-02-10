from fastapi import Request
from app.audit.audit_log_service import create_audit_log
from app.enums import AuditAction, AuditStatus
from app.routers.aduser_router import disable_user
from app.schemas import AuditLogCreate
from app.models.ad_user_model import DisableUserRequest
from app.services import intouch_service, email_service, turnstiles_service
from app.enums import EmailActions


async def execute_offboarding(registration, current_user, ad_service, background_tasks, req: Request, db):
    services_list = []
    
    
    try:
        res_turnstiles = await turnstiles_service.deactivate_user_turnstiles(registration=registration)
        if res_turnstiles.get("success"):
            services_list.append("Gate")
            
            create_audit_log(
                db,
                AuditLogCreate(
                    action=AuditAction.DISABLE_TURNSTILE_USER,
                    status=AuditStatus.SUCCESS,
                    message="User successfully blocked in all turnstiles.",
                    user_id=current_user.id,
                    username=current_user.username,
                    resource=registration,
                    ip_address=req.client.host if req.client else None,
                    user_agent=req.headers.get("user-agent"),
                ),
            )
    except Exception as e:
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.DISABLE_TURNSTILE_USER,
                status=AuditStatus.FAILED,
                message=f"Failure in turnstile deactivation: {str(e)}",
                user_id=current_user.id,
                username=current_user.username,
                resource=registration,
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("user-agent"),
            ),
        )

  
    try:
        res_intouch = await intouch_service.deactivate_user_intouch(registration)
        if res_intouch.get("success"):
            services_list.append("Intouch")
            
            create_audit_log(db, AuditLogCreate(
                action=AuditAction.DISABLE_INTOUCH_USER,
                status=AuditStatus.SUCCESS,
                message="User successfully deactivated from intouch.",
                user_id=current_user.id,
                username=current_user.username,
                resource=registration,
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("user-agent"),
            ))
    except Exception as e:
       
        create_audit_log(db, AuditLogCreate(
            action=AuditAction.DISABLE_INTOUCH_USER,
            status=AuditStatus.FAILED,
            message=f"Failure in Intouch deactivation: {str(e)}",
            user_id=current_user.id,
            username=current_user.username,
            resource=registration,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ))


    try:
        payload_ad = DisableUserRequest(registration=registration, performed_by=current_user.username)

        res_ad = ad_service.disable_user(payload_ad)
        services_list.append("Active Directory")
            
        create_audit_log(db, AuditLogCreate(
            action=AuditAction.DISABLE_AD_USER,
            status=AuditStatus.SUCCESS,
            message=f"User successfully deactivated from AD.",
            user_id=current_user.id,
            username=current_user.username,
            resource=registration,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ))
    except Exception as e:
        create_audit_log(db, AuditLogCreate(
            action=AuditAction.DISABLE_AD_USER,
            status=AuditStatus.FAILED,
            message=f"Failure in AD process: {str(e)}",
            user_id=current_user.id,
            username=current_user.username,
            resource=registration,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
        ))

    action_email = EmailActions.get_by_id(3)
    background_tasks.add_task(
        email_service.send_email,
        registration=registration,
        action=action_email,
        performed_by=str(current_user.username),
        systems_list=services_list
    )

    return {"success": True, "details": services_list}

