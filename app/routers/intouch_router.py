from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.security import Current_user, Editor_user
from app.services import intouch_service
from app.services.email_service import send_email

router = APIRouter(prefix="/intouch", tags=["Intouch"])


# AQUI FICA A ROTA DE CONSULTAR O USUARIO, UTILIZANDO A MATRICULA
@router.get("/{matricula}")
def consultar_usuario(
    current_user: Current_user,
    matricula: str
):
    resultado = intouch_service.buscar_funcionario(matricula)

    if not resultado:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Usuário não encontrado"
        )

    return resultado


# AQUI FICA A ROTA DE DESATIVAR O USUARIO, UTILIZANDO A MATRICULA
@router.post("/disable/{matricula}")
def desativar_funcionario(
    current_user: Current_user,
    matricula: str,
    background_tasks: BackgroundTasks
):
    resultado = intouch_service.desativar_funcionario(matricula)

    if not resultado:
        raise HTTPException(
            status_code=400, detail="Erro ao desativar usuário"
        )

    # EMAIL ENVIADO EM BACKGROUND PARA OTIMIZAR
    background_tasks.add_task(send_email, matricula, "desativado")

    return {
        "message": "Usuário desativado com sucesso",
        "matricula": matricula
    }

# AQUI FICA A ROTA DE ATIVAR O USUARIO, UTILIZANDO A MATRICULA
@router.post("/activate/{matricula}")
def ativar_funcionario(
    current_user: Current_user,
    matricula: str,
    background_tasks: BackgroundTasks
):
    resultado = intouch_service.ativar_funcionario(matricula)

    if not resultado.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=resultado.get("error", "Erro ao ativar usuário")
        )

    
    background_tasks.add_task(send_email, matricula, "ativado")

    return {
        "message": "Usuário ativado com sucesso",
        "matricula": matricula
    }
