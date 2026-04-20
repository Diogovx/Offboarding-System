from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    enabled: bool = True
    userRole: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: EmailStr | None = None
    enabled: bool | None = None
    userRole: UserRole | None = None

    model_config = ConfigDict(
        use_enum_values=True
    )


class UserPublic(UserBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]


class FilterPage(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)
