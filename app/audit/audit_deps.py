from typing import Annotated

from fastapi import Depends

from app.schemas import AuditLogListFilters


def audit_log_list_filters(
    filters: AuditLogListFilters = Depends()
) -> AuditLogListFilters:
    return filters


Audit_log_list_filters = Annotated[
    AuditLogListFilters,
    Depends(audit_log_list_filters)
]
