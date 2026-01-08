from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.audit.audit_model import AuditLog
from app.security import Admin_user, Db_session
from app.services import JSONLExporter, CSVExporter, fetch_audit_logs, create_audit_log
from app.schemas import AuditLogCreate
from typing import Literal
from app.enums import AuditAction, AuditStatus

router = APIRouter(prefix="/logs", tags=["Audit Logs"])


@router.get("/")
def list_logs(
    session: Db_session,
    _: Admin_user,
    action: AuditAction | None = Query(None),
    username: str | None = Query(None),
    status: AuditStatus | None = Query(None),
    limit: int = 100,
):
    result = fetch_audit_logs(
        session=session,
        action=action,
        username=username,
        status=status
    )

    return result


@router.get("/export")
def export_audit_logs(
    format: Literal["csv", "jsonl"],
    session: Db_session,
    current_user: Admin_user,
):
    logs = fetch_audit_logs(session)

    exporter = {
        "csv": CSVExporter(),
        "jsonl": JSONLExporter(),
    }[format]

    data = exporter.export(logs)

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.EXPORT_AUDIT_LOGS,
            status=AuditStatus.SUCCESS,
            message=f"Logs exported in {format} format",
            user_id=current_user.id,
            username=current_user.username,
            resource=format,
        ),
    )

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs.{format}"
        },
    )
