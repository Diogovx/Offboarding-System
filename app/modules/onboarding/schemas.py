# app/modules/onboarding/schemas.py

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from .enums import FieldType, ItemStatus, OnboardingStatus


# Free fields

class FieldCreate(BaseModel):
    """Payload to define a free-form field during checklist creation."""

    label:      str
    field_type: FieldType = FieldType.TEXT
    options:    str | None = None
    value:      str | None = None
    position:   int = 0
    required:   bool = False


class FieldRead(FieldCreate):
    """Serialized field for API responses."""

    id: int

    model_config = {"from_attributes": True}


# System Items

class ItemCreate(BaseModel):
    """Payload to define a system access task."""

    system_name: str
    description: str | None = None
    position:    int = 0


class ItemRead(ItemCreate):
    """Serialized item for API responses."""

    id:              int
    status:          ItemStatus
    completed_at:    datetime | None
    completed_by_id: UUID | None

    model_config = {"from_attributes": True}


class ItemComplete(BaseModel):
    """Payload sent by TI to mark an item as done or skipped."""

    status: ItemStatus = ItemStatus.DONE


# Checklist

class ChecklistCreate(BaseModel):
    """Payload to create a new onboarding checklist."""

    employee_name:         str
    employee_registration: str
    department:            str | None = None
    role:                  str | None = None
    start_date:            datetime | None = None
    notes:                 str | None = None
    fields:                list[FieldCreate] = Field(default_factory=list)
    items:                 list[ItemCreate] = Field(default_factory=list)


class ChecklistRead(BaseModel):
    """Full checklist representation for API responses."""

    id:                    int
    employee_name:         str
    employee_registration: str
    department:            str | None
    role:                  str | None
    start_date:            datetime | None
    notes:                 str | None
    status:                OnboardingStatus
    created_at:            datetime
    created_by_id:         UUID
    fields:                list[FieldRead]
    items:                 list[ItemRead]

    model_config = {"from_attributes": True}


class ChecklistSummary(BaseModel):
    """Lightweight checklist for list views."""

    id:                    int
    employee_name:         str
    employee_registration: str
    department:            str | None
    status:                OnboardingStatus
    created_at:            datetime
    total_items:           int
    completed_items:       int

    model_config = {"from_attributes": True}


class ChecklistListResponse(BaseModel):
    """Paginated response for checklist listings."""

    items: list[ChecklistSummary]
    total: int
    page:  int
    pages: int
