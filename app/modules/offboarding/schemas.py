from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class OffboardingContext(BaseModel):
    """Data required to record a completed offboarding process."""

    user_id: UUID
    username: str
    registration: str
    performed_by: str
    systems: list[str]


class RevokedSystemResult(BaseModel):
    """Result of a single system revocation attempt."""

    system: str
    success: bool
    message: str | None = None


class GeneratedTerm(BaseModel):
    """Represents a generated term document in Base64 format."""

    filename: str
    content_base64: str


class OffboardingResult(BaseModel):
    """Final result returned after executing a full offboarding."""

    success: bool
    details: list[str] = []
    terms: list[GeneratedTerm] = []
    error: str | None = None


class OffboardingHistoryItem(BaseModel):
    """Single offboarding record for history listing."""

    id: str
    username: str
    registration: str
    offboarded_at: datetime
    performed_by: str
    revoked_systems: list[str]


class OffboardingHistoryResponse(BaseModel):
    """Paginated offboarding history response."""

    items: list[OffboardingHistoryItem]
    total: int
    page: int
    pages: int
