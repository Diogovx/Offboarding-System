from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .model import OffboardingRecord, RevokedAccess
from .schemas import OffboardingContext, OffboardingHistoryItem, OffboardingHistoryResponse


def create_offboarding_record(
    session: Session,
    context: OffboardingContext,
) -> OffboardingRecord:
    """Creates an offboarding record and its associated revoked access entries.

    Args:
        session (Session): Active SQLAlchemy database session.
        context (OffboardingContext): Data describing the offboarding operation.

    Returns:
        OffboardingRecord: The persisted offboarding record.
    """
    record = OffboardingRecord(
        user_id=context.user_id,
        username=context.username,
        registration=context.registration,
        performed_by_username=context.performed_by,
    )
    session.add(record)
    session.flush()

    for system in context.systems:
        session.add(
            RevokedAccess(offboarding_id=record.id, system_name=system)
        )

    session.commit()
    session.refresh(record)
    return record


def get_offboarding_history(
    session: Session,
    *,
    registration: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> OffboardingHistoryResponse:
    """Retrieves paginated offboarding history, optionally filtered by registration.

    Args:
        session (Session): Active SQLAlchemy database session.
        registration (str | None): Employee registration number to filter by.
        page (int): Page number, starting at 1.
        limit (int): Maximum number of records per page.

    Returns:
        OffboardingHistoryResponse: Paginated list of offboarding records.
    """
    stmt = (
        select(OffboardingRecord)
        .order_by(OffboardingRecord.offboarded_at.desc())
    )

    if registration:
        stmt = stmt.where(OffboardingRecord.registration == registration)

    total = session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()

    records = session.execute(
        stmt.offset((page - 1) * limit).limit(limit)
    ).scalars().all()

    return OffboardingHistoryResponse(
        items=[_to_history_item(r) for r in records],
        total=total,
        page=page,
        pages=max(1, -(-total // limit)),
    )


def _to_history_item(record: OffboardingRecord) -> OffboardingHistoryItem:
    """Converts an ORM record to a serializable history item schema.

    Args:
        record (OffboardingRecord): SQLAlchemy ORM instance.

    Returns:
        OffboardingHistoryItem: Serializable Pydantic schema.
    """
    return OffboardingHistoryItem(
        id=str(record.id),
        username=record.username,
        registration=record.registration,
        offboarded_at=record.offboarded_at,
        performed_by=record.performed_by_username,
        revoked_systems=[a.system_name for a in record.revoked_accesses],
    )
