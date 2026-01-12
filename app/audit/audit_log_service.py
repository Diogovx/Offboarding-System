import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.audit_model import AuditLog
from app.audit.exporters import CSVExporter, JSONLExporter
from app.database import SessionLocal
from app.schemas import AuditLogCreate, AuditLogListFilters

from .audit_serializer import audit_log_to_dict

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
) -> list[dict]:
    offset = (filters.page - 1) * filters.limit

    stmt = select(AuditLog)

    if filters.action:
        stmt = stmt.where(AuditLog.action == filters.action)

    if filters.username:
        stmt = stmt.where(AuditLog.username == filters.username)

    if filters.status:
        stmt = stmt.where(AuditLog.status == filters.status)

    if filters.date_from:
        stmt = stmt.where(AuditLog.created_at >= filters.date_from)

    if filters.date_to:
        stmt = stmt.where(AuditLog.created_at <= filters.date_to)

    stmt = (
        stmt
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(filters.limit)
    )

    logs = session.execute(stmt).scalars().all()

    return [audit_log_to_dict(log) for log in logs]


def export_audit_logs_task(
    *,
    format: str,
    filters: AuditLogListFilters,
    filename: str,
):
    session = SessionLocal()
    try:
        logs = fetch_audit_logs(session=session, filters=filters)

        exporter = {
            "csv": CSVExporter(),
            "jsonl": JSONLExporter(),
        }[format]

        data = exporter.export(logs)

        file_path = EXPORT_DIR / filename
        file_path.write_bytes(data)
    except Exception as exc:
        print(f"[EXPORT ERROR] {exc}")
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
    ALLOWED_EXTENSIONS = {".csv", ".jsonl", ".zip"}

    filename = validate_filename(filename)

    base_dir = EXPORT_DIR.resolve()
    file_path = (base_dir / filename).resolve()

    if not str(file_path).startswith(str(base_dir)):
        raise ValueError("Path traversal detected")

    if file_path.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Extension not allowed")

    return file_path
