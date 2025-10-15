from pydantic import BaseModel

class User(BaseModel):
    Name: str
    SamAccountName: str
    Enabled: bool