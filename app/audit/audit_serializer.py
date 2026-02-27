from app.audit.audit_model import AuditLog


def audit_log_to_dict(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "action": log.action,
        "status": log.status,
        "username": log.username,
        "user_id": str(log.user_id) if log.user_id else None,
        "target_username": log.target_username,
        "target_registration": log.target_registration,
        "resource": log.resource,
        "message": log.message,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
