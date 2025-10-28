from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from subprocess import run, PIPE, STDOUT
import json
from .models import ADUser, User
from .database import init_db, get_db
from .security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def root():
    return { 
        "status": "online", 
        "version": "v1.0.0",
        "docs": "/docs" 
    }
    
@app.get("/aduser", response_model=list[ADUser])
async def get_user(username: str | None = None):
    if not username:
        filter_str = "*"
    else:
        safe_username = username.replace('"', '\"')
        filter_str = f"Name -like '*{safe_username}*'"
    
    command_args = [
        "powershell.exe",
        "-NonInteractive",
        "-Command",
        f"Get-AdUser -Filter \"{filter_str}\" -Properties SamAccountName,Name,Enabled | ConvertTo-Json -Compress"
    ]
    
    command_output = run(command_args, stdout=PIPE, stderr=STDOUT)
    
    output_string = command_output.stdout.decode('utf-8', errors='ignore').strip()
    
    try:
        json_data = json.loads(output_string)
        
        if isinstance(json_data, dict):
            users_list = [json_data]
        elif isinstance(json_data, list):
            users_list = json_data
        else:
            users_list = []
        
        return [ADUser.model_validate(user) for user in users_list]
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar Active Directory."
        )
        

@app.post("/test-user")
def create_user(db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.username == "test-user").first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário 'test-user' já existe."
        )
    
    hashed_pwd = get_password_hash('123')
    
    user = User(username="test-user", email="admin@test.com", password=hashed_pwd, enabled=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user