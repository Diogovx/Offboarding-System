from pydantic import BaseModel

class IFSUserResponse(BaseModel):
    success: bool = False
    found: bool = False
    id_system: str | None = None
    Etag: str | None = None
    name: str = ""
    Identify: str | None = None
    Description: str | None = None
    current_status: str | None = None
    is_active: bool = False
    error: str | None = None
    validFrom: str = ""
    validTo: str = ""

class IFSTokenRequest(BaseModel):
     
    response_type: str = "id_token token"
    grant_type: str = "password"
    scope: str = "openid"
    username: str
    password: str  
    client_id: str
    client_secret: str
   

class IFSTokenResponse(BaseModel):
    access_token: str  
    refresh_token: str | None = None  
    id_token: str | None = None
    token_type: str
    expires_in: int | str 