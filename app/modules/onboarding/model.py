import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime, Enum, ForeignKey, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.users.model import SqliteUUID, table_registry
from .enums import FieldType, ItemStatus, OnboardingStatus


@table_registry.mapped_as_dataclass
class OnboardingChecklist:
    """Represents a single onboarding process opened by HR for a new employee."""

    __tablename__ = "onboarding_checklists"

    id: Mapped[int] = mapped_column(
        primary_key=True, init=False
    )

    employee_name: Mapped[str] = mapped_column(String(150))
    employee_registration: Mapped[str] = mapped_column(String(50), index=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        SqliteUUID, ForeignKey("users.id")
    )

    # Controle
    status: Mapped[str] = mapped_column(
        String(20), default=OnboardingStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, init=False, server_default=func.now(), onupdate=func.now()
    )

    fields: Mapped[list["OnboardingField"]] = relationship(
        back_populates="checklist",
        init=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OnboardingField.position",
    )
    items: Mapped[list["OnboardingItem"]] = relationship(
        back_populates="checklist",
        init=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OnboardingItem.position",
    )


@table_registry.mapped_as_dataclass
class OnboardingField:
    """A free-form field defined by HR to capture employee information."""

    __tablename__ = "onboarding_fields"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("onboarding_checklists.id", ondelete="CASCADE"), index=True
    )

    label: Mapped[str] = mapped_column(String(100))  # field name ex: "Ramal"
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[str | None] = mapped_column(
        Text, nullable=True  # for type=select: "op1,op2,op3"
    )
    field_type: Mapped[str] = mapped_column(
        String(20), default=FieldType.TEXT
    )
    position: Mapped[int] = mapped_column(default=0)  # exibition order
    required: Mapped[bool] = mapped_column(default=False)

    checklist: Mapped["OnboardingChecklist"] = relationship(
        back_populates="fields", init=False
    )


@table_registry.mapped_as_dataclass
class OnboardingItem:
    """A system access task that TI must complete during onboarding."""

    __tablename__ = "onboarding_items"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)

    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("onboarding_checklists.id", ondelete="CASCADE"), index=True
    )

    system_name: Mapped[str] = mapped_column(String(100))  # ex: "Network"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(default=0)

    status: Mapped[str] = mapped_column(
        String(20), default=ItemStatus.PENDING
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, init=False, nullable=True
    )
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        SqliteUUID, ForeignKey("users.id"), nullable=True, init=False
    )

    checklist: Mapped["OnboardingChecklist"] = relationship(
        back_populates="items", init=False
    )
