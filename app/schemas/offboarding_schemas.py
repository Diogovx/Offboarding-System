from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class OffboardingContext(BaseModel):
    user_id: UUID
    username: str
    registration: str
    performed_by: str
    systems: list[str]
