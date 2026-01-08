from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit_model import AuditLog
from app.security import Admin_user, Db_session

router = APIRouter(prefix="/logs", tags=["Audit Logs"])


@router.get("/")
def list_logs(
    db: Db_session,
    _: Admin_user,
    action: str | None = Query(None),
    username: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = 100,
):
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)

    if username:
        query = query.filter(AuditLog.username == username)

    if status:
        query = query.filter(AuditLog.status == status)

    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
