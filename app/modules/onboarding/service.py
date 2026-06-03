from fastapi import Request
import logging
from sqlalchemy.orm import Session
from app.modules.audit.service import create_audit_log
from app.modules.audit.schemas import AuditLogCreate
from app.modules.audit.enums import AuditAction, AuditStatus
from app.modules.users import Current_user
from .enums import ItemStatus, OnboardingStatus
from .repository import (
    complete_item,
    create_checklist,
    get_checklist,
    list_checklists,
)
from .schemas import (
    ChecklistCreate,
    ChecklistListResponse,
    ChecklistRead,
)

logger = logging.getLogger(__name__)


def create_onboarding_checklist(
    session: Session,
    data: ChecklistCreate,
    request: Request,
    created_by_id,
    created_by_name,
) -> ChecklistRead:
    """Creates a new onboarding checklist on behalf of an HR user.

    Args:
        session (Session): Active database session.
        data (ChecklistCreate): Checklist payload from HR.
        created_by_id: UUID of the HR user creating the checklist.

    Returns:
        ChecklistRead: Full serialized checklist.
    """
    checklist = create_checklist(session, data, created_by_id)
    try:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.CREATE_CHECKLIST,
                status=AuditStatus.SUCCESS,
                message=f"Checklist of {checklist.employee_name} created",
                user_id=created_by_id,
                username=created_by_name,
                target_username=data.employee_name,
                target_registration=data.employee_registration,
                resource=str(checklist.id),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )
    except Exception as e:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.CREATE_CHECKLIST,
                status=AuditStatus.FAILED,
                message=f"Checklist creation failed: {e}",
                user_id=created_by_id,
                username=created_by_name,
                target_username=data.employee_name,
                target_registration=data.employee_registration,
                resource=str(checklist.id),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )

    logger.info(
        f"Checklist created for {data.employee_registration} "
        f"by {created_by_id} — {len(data.items)} system items."
    )
    return ChecklistRead.model_validate(checklist)


def get_onboarding_checklist(
    session: Session,
    checklist_id: int,
) -> ChecklistRead | None:
    """Retrieves a single checklist by ID.

    Args:
        session (Session): Active database session.
        checklist_id (int): Target checklist ID.

    Returns:
        ChecklistRead | None: Serialized checklist or None if not found.
    """
    checklist = get_checklist(session, checklist_id)
    if not checklist:
        return None
    return ChecklistRead.model_validate(checklist)


def fetch_checklists(
    session: Session,
    *,
    status: OnboardingStatus | None = None,
    registration: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> ChecklistListResponse:
    """Returns paginated checklists with optional filters.

    Args:
        session (Session): Active database session.
        status (OnboardingStatus | None): Filter by status.
        registration (str | None): Filter by employee registration.
        page (int): Page number.
        limit (int): Items per page.

    Returns:
        ChecklistListResponse: Paginated summary list.
    """
    return list_checklists(
        session,
        status=status,
        registration=registration,
        page=page,
        limit=limit,
    )


def mark_item_complete(
    session: Session,
    item_id: int,
    status: ItemStatus,
    completed_by_id,
) -> ChecklistRead | None:
    """Marks a system item as done or skipped and returns the updated checklist

    Args:
        session (Session): Active database session.
        item_id (int): ID of the item to update.
        status (ItemStatus): DONE or SKIPPED.
        completed_by_id: UUID of the TI user completing the item.

    Returns:
        ChecklistRead | None: Updated parent checklist or None if item not found.
    """
    item = complete_item(session, item_id, status, completed_by_id)
    if not item:
        return None
    logger.info(f"Item {item_id} marked as {status} by {completed_by_id}.")
    return ChecklistRead.model_validate(item.checklist)
