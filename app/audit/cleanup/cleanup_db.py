from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.audit.audit_model import AuditLog
from app.database import SessionLocal
from app.security import RETENTION_POLICY


def cleanup_audit_logs_db() -> int:
    session: Session = SessionLocal()
    total_deleted = 0

    try:
        now = datetime.now(timezone.utc)

        for action, delta in RETENTION_POLICY.items():
            cutoff = (now - delta).replace(tzinfo=None)

            count = session.scalar(
                select(func.count())
                .select_from(AuditLog)
                .where(AuditLog.action == action)
                .where(AuditLog.created_at < cutoff)
            ) or 0
            print("[CLEANUP DB]", action, count)

            session.execute(
                delete(AuditLog)
                .where(AuditLog.action == action)
                .where(AuditLog.created_at < cutoff)
            )
            total_deleted += count

        session.commit()
        return total_deleted

    finally:
        session.close()
