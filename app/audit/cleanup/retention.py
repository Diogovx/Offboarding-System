from datetime import timedelta
from app.enums import AuditAction

RETENTION_POLICY = {
    AuditAction.EXPORT_AUDIT_LOGS: timedelta(days=180),
    AuditAction.SYSTEM_LOGIN: timedelta(days=90),
    AuditAction.SYSTEM_LOGOUT: timedelta(days=90),
    AuditAction.CREATE_USER: timedelta(days=180),
    AuditAction.LIST_USERS: timedelta(days=90),
    AuditAction.SEARCH_AD_USER: timedelta(days=90),
    AuditAction.DISABLE_AD_USER: timedelta(days=365),
}
