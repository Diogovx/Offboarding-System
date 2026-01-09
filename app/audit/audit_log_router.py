from fastapi import APIRouter, Depends, Query, Response, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.audit.audit_model import AuditLog
from app.security import Admin_user, Db_session
from app.services import fetch_audit_logs, create_audit_log, export_audit_logs_task, safe_export_path
from app.schemas import AuditLogCreate
from typing import Literal
from app.enums import AuditAction, AuditStatus
from datetime import datetime, timedelta, date
from uuid import uuid4
from pathlib import Path


router = APIRouter(prefix="/logs", tags=["Audit Logs"])


@router.get("/")
def list_logs(
    session: Db_session,
    _: Admin_user,
    action: AuditAction | None = Query(None),
    username: str | None = Query(None),
    status: AuditStatus | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to:datetime | None = Query(None),
    page: int = 1,
    limit: int = 100,
):
    limit_days = 90
    if date_from and date_to:
        if date_to < date_from:
            raise HTTPException(
                status_code=400,
                detail="date_to must be after date_from"
            )

        if (date_to - date_from).days > limit_days:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 90 days"
            )
    if date_from and not date_to:
        date_to = date_from + timedelta(days=1)

    result = fetch_audit_logs(
        session=session,
        action=action,
        username=username,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit
    )

    return result


@router.post("/export")
def export_audit_logs_async(
    background_tasks: BackgroundTasks,
    format: Literal["csv", "jsonl"],
    session: Db_session,
    current_user: Admin_user,
    request: Request,
    action: AuditAction | None = Query(None),
    username: str | None = Query(None),
    status: AuditStatus | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10000, ge=1, le=50000),
):
    limit_days = 90
    if date_from and date_to:
        if date_to < date_from:
            raise HTTPException(
                status_code=400,
                detail="date_to must be after date_from"
            )

        if (date_to - date_from).days > limit_days:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 90 days"
            )
    if date_from and not date_to:
        date_to = date_from + timedelta(days=1)

    job_id = uuid4().hex
    filename = f"audit_logs_{job_id}.{format}"

    filters = dict(
        action=action,
        username=username,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )

    background_tasks.add_task(
        export_audit_logs_task,
        format=format,
        filters=filters,
        filename=filename,
    )

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.EXPORT_AUDIT_LOGS,
            status=AuditStatus.SUCCESS,
            message=f"Audit log export started ({format} format)",
            user_id=current_user.id,
            username=current_user.username,
            resource=filename,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        ),
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "format": format,
        "download_url": f"/logs/export/{filename}",
        "message": "Export is being processed. Check download_url in a few moments."
    }


@router.get("/export/{filename}")
def download_export(
    filename: str,
    _: Admin_user,
    request: Request,
    session: Db_session
):
    try:
        file_path = safe_export_path(filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not ready")
    except:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.EXPORT_AUDIT_LOGS,
                status=AuditStatus.FAILED,
                message=f"Path traversal attempt detected: {filename}",
                user_id=_.id,
                username=_.username,
                resource=filename,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            ),
        )
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename,
    )
