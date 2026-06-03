import logging
from fastapi import APIRouter, HTTPException, Query, Request

from app.modules.users import Current_user
from app.core.database import Db_session

from .enums import ItemStatus, OnboardingStatus
from .schemas import (
    ChecklistCreate,
    ChecklistListResponse,
    ChecklistRead,
    ItemComplete,
)
from .service import (
    create_onboarding_checklist,
    fetch_checklists,
    get_onboarding_checklist,
    mark_item_complete,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post(
    "/checklists",
    status_code=201,
    summary="Create a new onboarding checklist",
)
def create_checklist(
    data: ChecklistCreate,
    session: Db_session,
    request: Request,
    current_user: Current_user,
) -> ChecklistRead:
    """Creates an onboarding checklist with free-form fields and system access items.

    Args:
        data (ChecklistCreate): Checklist payload including employee info,
            custom fields and systems to provision.
        session (Db_session): Database session injected by FastAPI.
        current_user (Current_user): Authenticated HR user.

    Returns:
        ChecklistRead: Fully serialized created checklist.
    """
    return create_onboarding_checklist(session, data, request, current_user.id, current_user.username)


@router.get(
    "/checklists",
    summary="List onboarding checklists",
)
def list_checklists(
    session: Db_session,
    current_user: Current_user,
    status: OnboardingStatus | None = Query(default=None),
    registration: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ChecklistListResponse:
    """Returns a paginated list of onboarding checklists.

    Args:
        session (Db_session): Database session injected by FastAPI.
        current_user (Current_user): Authenticated user (RH or TI).
        status (OnboardingStatus | None): Optional status filter.
        registration (str | None): Optional registration number filter.
        page (int): Page number.
        limit (int): Items per page.

    Returns:
        ChecklistListResponse: Paginated checklist summaries.
    """
    return fetch_checklists(
        session,
        status=status,
        registration=registration,
        page=page,
        limit=limit,
    )


@router.get(
    "/checklists/{checklist_id}",
    summary="Get a single checklist",
)
def get_checklist(
    checklist_id: int,
    session: Db_session,
    current_user: Current_user,
) -> ChecklistRead:
    """Returns full detail of a single onboarding checklist.

    Args:
        checklist_id (int): Target checklist ID.
        session (Db_session): Database session injected by FastAPI.
        current_user (Current_user): Authenticated user.

    Returns:
        ChecklistRead: Full checklist with fields and items.

    Raises:
        HTTPException: 404 if checklist not found.
    """
    checklist = get_onboarding_checklist(session, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found.")
    return checklist


@router.patch(
    "/checklists/items/{item_id}/complete",
    summary="Mark a system item as done or skipped",
)
def complete_item(
    item_id: int,
    payload: ItemComplete,
    session: Db_session,
    current_user: Current_user,
) -> ChecklistRead:
    """Allows TI to mark a system access item as done or skipped.

    Automatically updates the parent checklist status based on overall progress.

    Args:
        item_id (int): ID of the item to update.
        payload (ItemComplete): New status — DONE or SKIPPED.
        session (Db_session): Database session injected by FastAPI.
        current_user (Current_user): Authenticated TI user.

    Returns:
        ChecklistRead: Updated parent checklist reflecting new progress.

    Raises:
        HTTPException: 404 if item not found.
    """
    checklist = mark_item_complete(
        session,
        item_id=item_id,
        status=payload.status,
        completed_by_id=current_user.id,
    )
    if not checklist:
        raise HTTPException(status_code=404, detail="Item not found.")
    return checklist
