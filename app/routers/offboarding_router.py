from fastapi import APIRouter, BackgroundTasks, Request, Query

from app.database import Db_session
from app.security import Current_user, Admin_user
from app.services import (
    execute_offboarding,
    get_offboarding_history,
    ADService,
    ADServiceDep,
    search_user
)

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


@router.get("/search/{registration}")
async def search_services(
    registration: str,
    current_user: Current_user
):
    service_list: set[str] = set()

    ad_service = ADService()

    ad_req = ad_service.search_users(registration=registration)
    if ad_req:
        service_list.add("Rede")
    intouch_req = search_user(registration=registration)
    if intouch_req:
        service_list.add("InTouch")

    return service_list


@router.post("/execute/{registration}")
async def execute(
    registration: str,
    current_user: Current_user,
    background_tasks: BackgroundTasks,
    ad_service: ADServiceDep,
    request: Request,
    session: Db_session
):

    result = await execute_offboarding(
        registration=registration,
        current_user=current_user,
        background_tasks=background_tasks,
        ad_service=ad_service,
        req=request,
        session=session
    )

    return result


@router.get("/history")
def list_offboarding_history(
    session: Db_session,
    _: Admin_user,
    registration: str | None = Query(default=None, description="Filtrer by registration"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return get_offboarding_history(
        db=session,
        registration=registration,
        page=page,
        limit=limit,
    )
