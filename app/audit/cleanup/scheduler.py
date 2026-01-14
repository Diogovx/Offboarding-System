from apscheduler.schedulers.background import BackgroundScheduler

from app.audit.cleanup.cleanup_db import cleanup_audit_logs_db

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        cleanup_audit_logs_db,
        trigger="cron",
        hour=3,
        id="audit_cleanup",
        replace_existing=True,
    )

    scheduler.start()
