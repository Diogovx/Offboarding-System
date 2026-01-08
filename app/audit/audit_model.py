from sqlalchemy import String, func, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from app.models import table_registry, SqliteUUID


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
    resource: Mapped[str | None]

    ip_address: Mapped[str | None]
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
