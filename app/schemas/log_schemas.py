from pydantic import BaseModel
from uuid import UUID

class AuditLogCreate(BaseModel):
    action: str
    status: str
    message: str | None = None
    user_id: UUID | None = None
    username: str | None = None
    resource: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
