import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .user_model import SqliteUUID, table_registry


@table_registry.mapped_as_dataclass
class OffboardingRecord:
    __tablename__ = "offboarding_records"

    username: Mapped[str] = mapped_column(String(100))
    registration: Mapped[str] = mapped_column(String(50), index=True)

    offboarded_at: Mapped[datetime] = mapped_column(
        DateTime, init=False, server_default=func.now(), index=True
    )
    performed_by_username: Mapped[str] = mapped_column(String(100))

    user_id: Mapped[uuid.UUID] = mapped_column(
        SqliteUUID, ForeignKey("users.id"), index=True
    )
    id: Mapped[int] = mapped_column(
        primary_key=True, init=False
    )

    revoked_accesses: Mapped[list["RevokedAccess"]] = relationship(
        back_populates="offboarding",
        init=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


@table_registry.mapped_as_dataclass
class RevokedAccess:
    __tablename__ = "revoked_accesses"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    offboarding_id: Mapped[int] = mapped_column(
        ForeignKey("offboarding_records.id", ondelete="CASCADE"),
        index=True
    )

    system_name: Mapped[str] = mapped_column(String(100))

    revoked_at: Mapped[datetime] = mapped_column(
        DateTime, init=False, server_default=func.now()
    )

    offboarding: Mapped["OffboardingRecord"] = relationship(
        back_populates="revoked_accesses", init=False
    )
