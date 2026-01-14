from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.audit.audit_log_service import EXPORT_DIR

EXPORT_DIR = Path(EXPORT_DIR)

EXPORT_RETENTION = {
    "csv": timedelta(days=30),
    "jsonl": timedelta(days=60),
}


def cleanup_export_files() -> int:
    now = datetime.now(timezone.utc)
    deleted = 0

    for file in EXPORT_DIR.iterdir():
        if not file.is_file():
            continue

        ext = file.suffix.lstrip(".")
        retention = EXPORT_RETENTION.get(ext)

        if not retention:
            continue

        created_at = datetime.fromtimestamp(
        file.stat().st_mtime,
            tz=timezone.utc,
        )

        if created_at < now - retention:
            file.unlink(missing_ok=True)
            deleted += 1

    return deleted
