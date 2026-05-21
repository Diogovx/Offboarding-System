from pydantic import BaseModel, Field

class IFSUserResponse(BaseModel):
    context: str | None = Field(None, alias="@odata.context")
    etag: str | None = Field(None, alias="@odata.etag")
    
    Identity: str
    Description: str | None = None
    Active: str | None = None
    ValidFrom: str | None = None
    ValidTo: str | None = None
    success: bool = True
    found: bool = True

    # be boolean
    @property
    def is_active(self) -> bool:
        return self.Active == "TRUE"

class IFSUserRequest(BaseModel):
    Etag: str | None = None
    Identify: str | None = None
    Description: str | None = None
    Active: str | None = None
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

class IFSPersonItem(BaseModel):
    PersonId: str 
    AlternativeName: str | None = None

class IFSPersonUserResponse(BaseModel):
    value: list[IFSPersonItem] = []

class IFSDesactiveUserRequest(BaseModel):
    Active: str
    