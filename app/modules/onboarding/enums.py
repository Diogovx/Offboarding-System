from enum import StrEnum


class OnboardingStatus(StrEnum):
    """Overall status of an onboarding checklist."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ItemStatus(StrEnum):
    """Status of a single system access item."""

    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"


class FieldType(StrEnum):
    """Type of a free-form field defined by HR."""

    TEXT = "text"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
