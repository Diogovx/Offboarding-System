from pydantic import BaseModel


class ADUser(BaseModel):
    name: str
    sam_account_name: str
    enabled: bool
    distinguished_name: str
    description: str | None


class DisableUserRequest(BaseModel):
    registration: str
    performed_by: str
