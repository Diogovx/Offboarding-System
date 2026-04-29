from fastapi import APIRouter, BackgroundTasks, Request, Query

from app.core.database import Db_session
from app.core import Current_user
from app.integrations.active_directory import ADServiceDep
from .service import (
    execute_offboarding,
    get_offboarding_history,
    verify_services_before_disabling
)

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


@router.get("/search/{registration}")
async def search_services(
    registration: str,
    current_user: Current_user
) -> dict[str, bool]:

    return await verify_services_before_disabling(registration)


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
    _: Current_user,
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
