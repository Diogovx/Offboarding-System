from app.audit.cleanup.cleanup_db import cleanup_audit_logs_db
from app.audit.cleanup.cleanup_files import cleanup_export_files
import logging

logger = logging.getLogger(__name__)


def run_audit_cleanup():
    db_deleted = cleanup_audit_logs_db()
    files_deleted = cleanup_export_files()

    logger.info(
        "Audit cleanup completed",
        extra={
            "db_deleted": db_deleted,
            "files_deleted": files_deleted,
        }
    )
