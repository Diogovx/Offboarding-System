from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.enums import AuditAction, AuditStatus


class AuditLogCreate(BaseModel):
    action: str
    status: str
    message: str | None = None
    user_id: UUID | None = None
    username: str | None = None
    target_user_id: str | None = None
    target_username: str | None = None
    target_registration: str | None = None
    resource: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogListFilters(BaseModel):
    action: AuditAction | None = None
    username: str | None = None
    status: AuditStatus | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    limit: int = 100


class ExportContext(BaseModel):
    format: Literal["csv", "jsonl", "pdf", "xlsx"]
    filters: AuditLogListFilters


class AuditLogList(BaseModel):
    items: list[dict]
    total: int | None
    page: int
    limit: int
    pages: int


class AuditLogExportedStatus(BaseModel):
    job_id: str
    status: str
    format: Literal["csv", "jsonl", "pdf", "xlsx"]
    download_url: str
    message: str
