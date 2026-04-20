from pydantic import BaseModel
from app.models import ADUser


class ADUserDisableResponse(BaseModel):
    success: bool
    action: str
    user: ADUser
    message: str
