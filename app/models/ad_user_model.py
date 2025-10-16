from pydantic import BaseModel

class ADUser(BaseModel):
    Name: str
    SamAccountName: str
    Enabled: bool