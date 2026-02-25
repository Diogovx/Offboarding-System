from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse

from app.database import Db_session
from app.enums import AuditAction, AuditStatus
from app.schemas import (
    AuditLogCreate,
    ExportContext,
    AuditLogList,
    AuditLogExportedStatus
)
from app.security import Admin_user, Audit_log_list_filters
from app.services import (
    create_audit_log,
    export_audit_logs_task,
    fetch_audit_logs,
    safe_export_path,
)

router = APIRouter(prefix="/logs", tags=["Audit Logs"])


@router.get("/")
def list_logs(
    session: Db_session,
    _: Admin_user,
    filters: Audit_log_list_filters
) -> AuditLogList:
    limit_days = 90
    if filters.date_from and filters.date_to:
        if filters.date_to < filters.date_from:
            raise HTTPException(
                status_code=400,
                detail="date_to must be after date_from"
            )

        if (filters.date_to - filters.date_from).days > limit_days:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 90 days"
            )
    if filters.date_from and not filters.date_to:
        filters.date_to = filters.date_from + timedelta(days=1)

    result = fetch_audit_logs(
        session=session,
        filters=filters
    )

    return result


@router.post("/export")
def export_audit_logs_async(
    context: ExportContext,
    background_tasks: BackgroundTasks,
    session: Db_session,
    current_user: Admin_user,
    request: Request,
) -> AuditLogExportedStatus:
    limit_days = 90
    if context.filters.date_from and context.filters.date_to:
        if context.filters.date_to < context.filters.date_from:
            raise HTTPException(
                status_code=400,
                detail="date_to must be after date_from"
            )

        if (
            context.filters.date_to - context.filters.date_from
        ).days > limit_days:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 90 days"
            )
    if context.filters.date_from and not context.filters.date_to:
        context.filters.date_to = context.filters.date_from + timedelta(days=1)

    job_id = uuid4().hex
    filename = f"audit_logs_{job_id}.{context.format}"

    background_tasks.add_task(
        export_audit_logs_task,
        format=context.format,
        filters=context.filters,
        filename=filename,
    )

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.EXPORT_AUDIT_LOGS,
            status=AuditStatus.SUCCESS,
            message=f"Audit log export started ({context.format} format)",
            user_id=current_user.id,
            username=current_user.username,
            resource=filename,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        ),
    )

    return AuditLogExportedStatus(
        job_id=job_id,
        status="processing",
        format=context.format,
        download_url=f"/logs/export/{filename}",
        message='''Export is being processed.
        Check download_url in a few moments.'''
    )


@router.get("/export/{filename}")
def download_export(
    filename: str,
    current_user: Admin_user,
    request: Request,
    session: Db_session
) -> FileResponse:
    try:
        file_path = safe_export_path(filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not ready")
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.EXPORT_AUDIT_LOGS,
                status=AuditStatus.FAILED,
                message=f"File not ready: {filename}",
                user_id=current_user.id,
                username=current_user.username,
                resource=filename,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            ),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
