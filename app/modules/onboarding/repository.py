# app/modules/onboarding/repository.py

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .enums import ItemStatus, OnboardingStatus
from .model import OnboardingChecklist, OnboardingField, OnboardingItem
from .schemas import ChecklistCreate, ChecklistListResponse, ChecklistSummary

from datetime import datetime


def create_checklist(
    session: Session,
    data: ChecklistCreate,
    created_by_id,
) -> OnboardingChecklist:
    """Creates a checklist with its fields and system items in a single transaction.

    Args:
        session (Session): Active database session.
        data (ChecklistCreate): Payload from HR containing employee info,
            free-form fields and system access items.
        created_by_id: UUID of the HR user creating the checklist.

    Returns:
        OnboardingChecklist: Persisted checklist with all relationships loaded.
    """
    checklist = OnboardingChecklist(
        employee_name=data.employee_name,
        employee_registration=data.employee_registration,
        department=data.department,
        role=data.role,
        start_date=data.start_date,
        notes=data.notes,
        created_by_id=created_by_id,
    )
    session.add(checklist)
    session.flush()

    for f in data.fields:
        session.add(OnboardingField(
            checklist_id=checklist.id,
            label=f.label,
            field_type=f.field_type,
            options=f.options,
            value=f.value,
            position=f.position,
            required=f.required,
        ))

    for i in data.items:
        session.add(OnboardingItem(
            checklist_id=checklist.id,
            system_name=i.system_name,
            description=i.description,
            position=i.position,
        ))

    session.commit()
    session.refresh(checklist)
    return checklist


def get_checklist(
    session: Session,
    checklist_id: int
) -> OnboardingChecklist | None:
    """Fetches a single checklist by ID with all relationships.

    Args:
        session (Session): Active database session.
        checklist_id (int): Primary key of the checklist.

    Returns:
        OnboardingChecklist | None: The checklist or None if not found.
    """
    return session.get(OnboardingChecklist, checklist_id)


def list_checklists(
    session: Session,
    *,
    status: OnboardingStatus | None = None,
    registration: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> ChecklistListResponse:
    """Returns a paginated summary list of checklists with optional filters.

    Args:
        session (Session): Active database session.
        status (OnboardingStatus | None): Filter by checklist status.
        registration (str | None): Filter by employee registration number.
        page (int): Page number starting at 1.
        limit (int): Records per page.

    Returns:
        ChecklistListResponse: Paginated summary list.
    """
    stmt = select(OnboardingChecklist).order_by(
        OnboardingChecklist.created_at.desc()
    )

    if status:
        stmt = stmt.where(OnboardingChecklist.status == status)
    if registration:
        stmt = stmt.where(OnboardingChecklist.employee_registration == registration)

    total = session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()

    records = session.execute(
        stmt.offset((page - 1) * limit).limit(limit)
    ).scalars().all()

    summaries = [
        ChecklistSummary(
            id=r.id,
            employee_name=r.employee_name,
            employee_registration=r.employee_registration,
            department=r.department,
            status=r.status,
            created_at=r.created_at,
            total_items=len(r.items),
            completed_items=sum(
                1 for i in r.items if i.status == ItemStatus.DONE
            ),
        )
        for r in records
    ]

    return ChecklistListResponse(
        items=summaries,
        total=total,
        page=page,
        pages=max(1, -(-total // limit)),
    )


def complete_item(
    session: Session,
    item_id: int,
    status: ItemStatus,
    completed_by_id,
) -> OnboardingItem | None:
    """Marks a single system item as done or skipped and updates checklist status.

    Automatically transitions the checklist to IN_PROGRESS on first completion
    and to COMPLETED when all items are resolved.

    Args:
        session (Session): Active database session.
        item_id (int): Primary key of the item to update.
        status (ItemStatus): New status — DONE or SKIPPED.
        completed_by_id: UUID of the TI user completing the item.

    Returns:
        OnboardingItem | None: Updated item or None if not found.
    """

    item = session.get(OnboardingItem, item_id)
    if not item:
        return None

    item.status = status
    item.completed_at = datetime.utcnow()
    item.completed_by_id = completed_by_id

    # Atualizar status do checklist automaticamente
    checklist = item.checklist
    all_items = checklist.items
    resolved = [i for i in all_items if i.status in (ItemStatus.DONE, ItemStatus.SKIPPED)]

    if len(resolved) == len(all_items):
        checklist.status = OnboardingStatus.COMPLETED
    elif len(resolved) > 0:
        checklist.status = OnboardingStatus.IN_PROGRESS

    session.commit()
    session.refresh(item)
    return item
