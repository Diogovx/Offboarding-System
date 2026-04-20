import uuid
from datetime import datetime

from sqlalchemy import BLOB, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator
from app.core import table_registry
from app.modules.shared import SqliteUUID
from .enums import UserRole




@table_registry.mapped_as_dataclass
class User:
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    userRole: Mapped[UserRole] = mapped_column(
        Integer, default=UserRole.USER, server_default=str(UserRole.USER.value)
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    id: Mapped[uuid.UUID] = mapped_column(
        SqliteUUID(),
        primary_key=True,
        default_factory=uuid.uuid4,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, init=False, server_default=func.now()
    )
