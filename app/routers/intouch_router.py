from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.security import Current_user, Editor_user
from app.services import intouch_service
from app.services.email_service import send_email
from app.enums import EmailActions



router = APIRouter(prefix="/intouch", tags=["Intouch"])


@router.get("/{matricula}")
async def consultar_usuario(
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


@router.post("/disable/{matricula}")
async def desativar_funcionario(
    current_user: Current_user,
    matricula: str,
    background_tasks: BackgroundTasks
):
    resultado = await intouch_service.desativar_funcionario(matricula)

    if not resultado:
        raise HTTPException(
            status_code=400, detail="Erro ao desativar usuário"
        )

    action = EmailActions.get_by_id(3)
    background_tasks.add_task(send_email, matricula, action)

    return {
        "message": "Usuário desativado com sucesso",
        "matricula": matricula
    }

@router.post("/activate/{matricula}")
async def ativar_funcionario(
    current_user: Current_user,
    matricula: str,
    background_tasks: BackgroundTasks
):
    resultado = await intouch_service.ativar_funcionario(matricula)

    if not resultado.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=resultado.get("error", "Erro ao ativar usuário")
        )

    action = EmailActions.get_by_id(2)
    background_tasks.add_task(send_email, matricula, action)

    return {
        "message": "Usuário ativado com sucesso",
        "matricula": matricula
    }
