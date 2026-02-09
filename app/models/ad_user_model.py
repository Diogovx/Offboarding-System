from pydantic import BaseModel, Field


class ADUser(BaseModel):
    name: str
    sam_account_name: str
    enabled: bool
    distinguished_name: str
    description: str | None
    user_account_control: int = Field(..., description="UAC from AD")


class DisableUserRequest(BaseModel):
    registration: str
    performed_by: str
