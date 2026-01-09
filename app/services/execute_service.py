from app.models.ad_user_model import DisableUserRequest
from app.routers import aduser_router
from app.services import intouch_service
from app.services.email_service import send_email
from app.enums import EmailActions

async def execute_offboarding(matricula, current_user, background_tasks):

    payload_ad = DisableUserRequest(
        registration=matricula,
        performed_by=current_user.username 
    )

    res_intouch =  await intouch_service.desativar_funcionario(matricula)
    res_ad = await aduser_router.disable_user(payload=payload_ad, session=current_user)
    
    if not res_intouch.get("success") or not res_ad.get("sucess"):
        error_msg = f"InTouch: {res_intouch.get('error')} | AD: {res_ad.get('error')}"
        return {"success": False, "error": error_msg}

   
    action = EmailActions.get_by_id(3)
    background_tasks.add_task(send_email, matricula, action)

  
    return {
        "success": True,
        "message": res_intouch.get("message"),
        "acao": res_intouch.get("acao"),
        "details": {
            "intouch": res_intouch.get("message"),
            "ad": res_ad.get("message")
        }
    }