from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from app.enums import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    enabled: bool = True
    userRole: Optional[UserRole] = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None

class UserPublic(UserBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
class UserList(BaseModel):
    users: list[UserPublic]