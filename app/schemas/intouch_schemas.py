from pydantic import BaseModel


class InTouchUserSearchModel(BaseModel):
    success: bool = False
    found: bool = False
    id_system: str | None = None
    name: str = ""
    email: str | None = None
    role: str | None = None
    current_status: str | None = None
    is_active: bool = False
    registration: str = ""
    details: str = ""
    error: str | None = None


class InTouchActivateUserModel(BaseModel):
    success: bool = False
    message: str = ""
    action: str = ""
    error: str | None = None


class InTouchDeactivateUserModel(BaseModel):
    success: bool = False
    message: str = ""
    action: str = ""
    error: str | None = None
