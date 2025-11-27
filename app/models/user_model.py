import uuid
from datetime import datetime
from sqlalchemy import func, String, Boolean, Integer, DateTime, BLOB
from sqlalchemy.orm import Mapped, registry, mapped_column
from sqlalchemy.types import TypeDecorator
from ..enums import UserRole

table_registry = registry()


class SqliteUUID(TypeDecorator):
    impl = BLOB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(value).bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(bytes=value)


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
