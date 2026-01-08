from app.services import intouch_service
from app.services.email_service import send_email
from app.enums import EmailActions

async def execute_offboarding(matricula, current_user, background_tasks):
    resultado = intouch_service.desativar_funcionario(matricula)
    
    if not resultado.get("success"):
        return {"success": False, "error": resultado.get("error")}

   
    action = EmailActions.get_by_id(3)
    background_tasks.add_task(send_email, matricula, action)

  
    return {
        "success": True,
        "message": resultado.get("message"),
        "acao": resultado.get("acao")
    }