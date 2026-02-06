from enum import Enum


class AuditAction(str, Enum):
    SYSTEM_LOGIN = "system_login"
    SYSTEM_LOGOUT = "system_logout"
    TOKEN_REFRESH = "token_refresh"

    LIST_USERS = "list_users"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    READ_CURRENT_USER = "read_current_user"

    SEARCH_AD_USER = "search_ad_user"
    DISABLE_AD_USER = "disable_ad_user"

    SEARCH_INTOUCH_USER = "search_intouch_user"
    DISABLE_INTOUCH_USER = "disable_intouch_user"

    DISABLE_TURNSTILE_USER = "disable_turnstile_user"

    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_AUDIT_LOGS = "export_audit_logs"

    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
