# app/modules/offboarding/router.py

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response

from app.core.database import Db_session
from app.core import Current_user
from app.integrations.active_directory import ADServiceDep
from app.integrations.snipe_it import (
    CheckinAssetRequest,
    GenerateTermRequest,
    SnipeItService,
    get_snipeit_service,
)

from .schemas import OffboardingHistoryResponse, OffboardingResult
from .service import execute_offboarding, fetch_offboarding_history, verify_services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


@router.get(
    "/search/{registration}",
    summary="Check active systems for a given employee",
)
async def search_services(
    registration: str,
    current_user: Current_user,
    snipeit: SnipeItService = Depends(get_snipeit_service),
) -> dict[str, bool]:
    """Returns a map of external systems and whether the user is currently active in each.

    Args:
        registration (str): Employee registration number.
        current_user (Current_user): Authenticated user making the request.
        snipeit (SnipeItService): Snipe-IT service injected by FastAPI.

    Returns:
        dict[str, bool]: System name mapped to active status.
    """
    return await verify_services(registration, snipeit)


@router.post(
    "/execute/{registration}",
    summary="Execute full offboarding for an employee",
)
async def execute(
    registration: str,
    current_user: Current_user,
    background_tasks: BackgroundTasks,
    ad_service: ADServiceDep,
    request: Request,
    session: Db_session,
    snipeit_service: SnipeItService = Depends(get_snipeit_service),
) -> OffboardingResult:
    """Triggers the full offboarding sequence for the given registration.

    Revokes access across all active systems, generates checkin documents,
    persists the offboarding record, and dispatches a notification email.

    Args:
        registration (str): Employee registration number to offboard.
        current_user (Current_user): Authenticated user performing the operation.
        background_tasks (BackgroundTasks): FastAPI task queue for async email.
        ad_service (ADServiceDep): Active Directory service injected by FastAPI.
        request (Request): FastAPI request for audit metadata.
        session (Db_session): Database session injected by FastAPI.
        snipeit_service (SnipeItService): Snipe-IT service injected by FastAPI.

    Returns:
        OffboardingResult: Result with success status, affected systems, and term documents.
    """
    return await execute_offboarding(
        registration=registration,
        current_user=current_user,
        background_tasks=background_tasks,
        ad_service=ad_service,
        snipeit_service=snipeit_service,
        req=request,
        session=session,
    )


@router.get(
    "/history",
    summary="List offboarding history",
)
def list_history(
    session: Db_session,
    _: Current_user,
    registration: str | None = Query(default=None, description="Filter by registration number"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Records per page"),
) -> OffboardingHistoryResponse:
    """Returns paginated offboarding history, optionally filtered by registration.

    Args:
        session (Db_session): Database session injected by FastAPI.
        _ (Current_user): Authenticated user (required but unused directly).
        registration (str | None): Optional registration number to filter records.
        page (int): Page number starting at 1.
        limit (int): Number of records per page, between 1 and 100.

    Returns:
        OffboardingHistoryResponse: Paginated list of offboarding records.
    """
    return fetch_offboarding_history(
        session,
        registration=registration,
        page=page,
        limit=limit,
    )


@router.post(
    "/generate-term",
    summary="Generate a term document for a specific asset",
)
async def generate_term(
    request: GenerateTermRequest,
    snipeit: SnipeItService = Depends(get_snipeit_service),
) -> Response:
    """Generates a DOCX term document for a given employee and asset tag.

    Args:
        request (GenerateTermRequest): Payload containing employee number,
            asset tag, and template ID.
        snipeit (SnipeItService): Snipe-IT service injected by FastAPI.

    Returns:
        Response: Binary DOCX file as a downloadable attachment.

    Raises:
        HTTPException: 500 if document generation fails.
    """
    try:
        docx_bytes = await snipeit.generate_term(
            employee_num=request.employee_num,
            asset_tag=request.asset_tag,
            template_id=request.template_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate term: {e}")

    filename = f"termo_{request.employee_num}_{request.asset_tag}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post(
    "/checkin",
    summary="Manually checkin an asset in Snipe-IT",
)
async def checkin_asset(
    payload: CheckinAssetRequest,
    snipeit: SnipeItService = Depends(get_snipeit_service),
) -> dict:
    """Manually returns a specific asset to inventory in Snipe-IT.

    Args:
        payload (CheckinAssetRequest): Registration number, asset tag, and optional note.
        snipeit (SnipeItService): Snipe-IT service injected by FastAPI.

    Returns:
        dict: Confirmation message and raw Snipe-IT API response.

    Raises:
        HTTPException: 404 if the user or asset is not found.
        HTTPException: 500 on internal or API failure.
    """
    try:
        result = await snipeit.checkin_asset(
            registration=payload.registration,
            asset_tag=payload.asset_tag,
            note=payload.note,
        )
        return {
            "success": True,
            "message": f"Asset {payload.asset_tag} successfully returned.",
            "data": result,
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkin failed: {e}")
