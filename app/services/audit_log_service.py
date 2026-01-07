from sqlalchemy.orm import Session
from app.schemas import AuditLogCreate
from app.models.audit_model import AuditLog


def create_audit_log(
    db: Session,
    data: AuditLogCreate
):
    log = AuditLog(**data.model_dump())

    db.add(log)
    db.commit()
