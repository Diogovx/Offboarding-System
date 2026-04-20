from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import SqliteUUID, table_registry


@table_registry.mapped
class AuditLog:
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str | None]
    user_id: Mapped[UUID | None] = mapped_column(
        SqliteUUID(),
        nullable=True
    )
    username: Mapped[str | None]

    target_user_id: Mapped[UUID | None] = mapped_column(
        SqliteUUID(), nullable=True
    )
    target_username: Mapped[str | None]
    target_registration: Mapped[str | None]
    resource: Mapped[str | None]

    ip_address: Mapped[str | None]
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
