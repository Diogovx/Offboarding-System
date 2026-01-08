from sqlalchemy.orm import Session
from app.schemas import AuditLogCreate 
from app.audit.audit_model import AuditLog
from app.enums import AuditAction, AuditStatus
from .audit_serializer import audit_log_to_dict

def create_audit_log(
    db: Session,
    data: AuditLogCreate
):
    log = AuditLog(**data.model_dump())

    db.add(log)
    db.commit()


def fetch_audit_logs(
    session: Session,
    action: AuditAction | None = None,
    username: str | None = None,
    status: AuditStatus | None = None,
    limit: int = 100,
):
    query = session.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)

    if username:
        query = query.filter(AuditLog.username == username)

    if status:
        query = query.filter(AuditLog.status == status)

    logs = (
        query
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [audit_log_to_dict(log) for log in logs]
