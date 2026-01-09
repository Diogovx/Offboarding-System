from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas import AuditLogCreate 
from datetime import datetime
from app.audit.audit_model import AuditLog
from app.enums import AuditAction, AuditStatus
from .audit_serializer import audit_log_to_dict
from pathlib import Path
from app.audit.exporters import CSVExporter, JSONLExporter
from app.database import SessionLocal
import re

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
    action: AuditAction | None = None,
    username: str | None = None,
    status: AuditStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    limit: int = 100,
) -> list[dict]:
    offset = (page - 1) * limit

    stmt = select(AuditLog)

    if action:
        stmt = stmt.where(AuditLog.action == action)

    if username:
        stmt = stmt.where(AuditLog.username == username)

    if status:
        stmt = stmt.where(AuditLog.status == status)

    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)

    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)

    stmt = (
        stmt
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    logs = session.execute(stmt).scalars().all()

    return [audit_log_to_dict(log) for log in logs]


def export_audit_logs_task(
    *,
    format: str,
    filters: dict,
    filename: str,
):
    session = SessionLocal()
    try:
        logs = fetch_audit_logs(session=session, **filters)

        exporter = {
            "csv": CSVExporter(),
            "jsonl": JSONLExporter(),
        }[format]

        data = exporter.export(logs)

        file_path = EXPORT_DIR / filename
        file_path.write_bytes(data)

    finally:
        session.close()


def validate_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Empty filename")

    if not FILENAME_RE.match(filename):
        raise ValueError("Filename contains invalid characters.s")

    return filename


def safe_export_path(filename: str) -> Path:
    ALLOWED_EXTENSIONS = {".csv", ".jsonl", ".zip"}

    filename = validate_filename(filename)

    base_dir = EXPORT_DIR.resolve()
    file_path = (base_dir / filename).resolve()

    if not str(file_path).startswith(str(base_dir)):
        raise ValueError("Path traversal detected")

    if file_path.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Extension not allowed")

    return file_path
