from pydantic import BaseModel


class ADUser(BaseModel):
    Name: str
    SamAccountName: str
    Enabled: bool
    DistinguishedName: str
    Description: str | None


class DisableUserRequest(BaseModel):
    registration: str
    performed_by: str
