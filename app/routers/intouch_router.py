from http import HTTPStatus
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.security import Current_user, Editor_user
from app.services import intouch_service
from app.services.email_service import send_email
from app.enums import EmailActions

router = APIRouter(prefix="/intouch", tags=["Intouch"])

@router.get("/{registration}")
async def consultar_usuario(
    current_user: Current_user,
    registration: str
):
    res_intouch = intouch_service.buscar_funcionario(registration)

    if not res_intouch:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found"
        )

    return res_intouch

@router.post("/disable/{registration}")
async def deactivate_user_intouch(
    current_user: Current_user,
    registration: str,
    background_tasks: BackgroundTasks
):
    res_intouch = await intouch_service.deactivate_user_intouch(registration)

    if not res_intouch:
        raise HTTPException(
            status_code=400, 
            detail="Error while deactivating user"
        )

    action = EmailActions.get_by_id(3)
    background_tasks.add_task(send_email, registration, action)

    return {
        "message": "User successfully deactivated",
        "registration": registration
    }

@router.post("/activate/{registration}")
async def activate_user_intouch(
    current_user: Current_user,
    registration: str,
    background_tasks: BackgroundTasks
):
    res_intouch = await intouch_service.activate_user_intouch(registration)

    if not res_intouch.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=res_intouch.get("error", "Error while activating user")
        )

    action = EmailActions.get_by_id(2)
    background_tasks.add_task(send_email, registration, action)

    return {
        "message": "User successfully activated",
        "registration": registration
    }