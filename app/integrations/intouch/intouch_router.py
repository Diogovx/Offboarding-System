from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.enums import EmailActions
from app.core.security import Current_user
from app.integrations.intouch import service
from app.modules.shared.email_service import send_email

router = APIRouter(prefix="/intouch", tags=["Intouch"])


@router.get("/{registration}")
async def search_user(
    current_user: Current_user,
    registration: str
):
    res_intouch = service.search_user(registration)

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
    res_intouch = await service.deactivate_user_intouch(registration)

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
    res_intouch = await service.activate_user_intouch(registration)

    if not res_intouch.success:
        raise HTTPException(
            status_code=400,
            detail=res_intouch.error
        )

    action = EmailActions.get_by_id(2)
    background_tasks.add_task(send_email, registration, action)

    return {
        "message": "User successfully activated",
        "registration": registration
    }
