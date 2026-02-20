import re
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from logging import getLogger

from app.audit.audit_model import AuditLog
from app.audit.exporters import CSVExporter, JSONLExporter, PDFExporter, XLSXExporter
from app.database import SessionLocal
from app.schemas import AuditLogCreate, AuditLogListFilters, AuditLogList
from .audit_serializer import audit_log_to_dict

logger = getLogger(__name__)

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)
FILENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def create_audit_log(
    db: Session,
    data: AuditLogCreate
):
    log = AuditLog(**data.model_dump())

    db.add(log)
    db.commit()


def fetch_audit_logs(
    session: Session,
    *,
    filters: AuditLogListFilters
) -> AuditLogList:
    offset = (filters.page - 1) * filters.limit

    base_stmt = select(AuditLog)

    if filters.action:
        base_stmt = base_stmt.where(AuditLog.action == filters.action)

    if filters.username:
        base_stmt = base_stmt.where(AuditLog.username == filters.username)

    if filters.status:
        base_stmt = base_stmt.where(AuditLog.status == filters.status)

    if filters.date_from:
        base_stmt = base_stmt.where(AuditLog.created_at >= filters.date_from)

    if filters.date_to:
        base_stmt = base_stmt.where(AuditLog.created_at <= filters.date_to)

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = session.execute(count_stmt).scalar() or 0

    stmt = (
        base_stmt
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(filters.limit)
    )

    logs = session.execute(stmt).scalars().all()

    return AuditLogList(
        items=[audit_log_to_dict(log) for log in logs],
        total=total,
        page=filters.page,
        limit=filters.limit,
        pages=(total // filters.limit) + (1 if total % filters.limit else 0)
    )


def fetch_all_logs_for_export(session: Session, filters: AuditLogListFilters):
    base_stmt = select(AuditLog)

    if filters.action:
        base_stmt = base_stmt.where(AuditLog.action == filters.action)

    if filters.username:
        base_stmt = base_stmt.where(AuditLog.username == filters.username)

    if filters.status:
        base_stmt = base_stmt.where(AuditLog.status == filters.status)

    if filters.date_from:
        base_stmt = base_stmt.where(AuditLog.created_at >= filters.date_from)

    if filters.date_to:
        base_stmt = base_stmt.where(AuditLog.created_at <= filters.date_to)

    logs = session.execute(
        base_stmt.order_by(AuditLog.created_at.desc())
    ).scalars().all()

    return [audit_log_to_dict(log) for log in logs]


def export_audit_logs_task(
    *,
    format: str,
    filters: AuditLogListFilters,
    filename: str,
):
    session = SessionLocal()
    try:
        logs = fetch_all_logs_for_export(session, filters)

        exporter = {
            "csv": CSVExporter(),
            "jsonl": JSONLExporter(),
            "pdf": PDFExporter(),
            "xlsx": XLSXExporter(),
        }[format]

        data = exporter.export(logs)

        file_path = EXPORT_DIR / filename
        file_path.write_bytes(data)
    except Exception as e:
        logger.error(f"EXPORT ERROR: {e}")
        raise
    finally:
        session.close()


def validate_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Empty filename")

    if not FILENAME_RE.match(filename):
        raise ValueError("Filename contains invalid characters.s")

    return filename


def safe_export_path(filename: str) -> Path:
    ALLOWED_EXTENSIONS = {".csv", ".jsonl", ".xlsx", ".pdf"}

    filename = validate_filename(filename)

    base_dir = EXPORT_DIR.resolve()
    file_path = (base_dir / filename).resolve()

    if not str(file_path).startswith(str(base_dir)):
        raise ValueError("Path traversal detected")

    if file_path.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Extension not allowed")

    return file_path
