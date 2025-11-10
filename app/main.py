from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from http import HTTPStatus
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from subprocess import run, PIPE, STDOUT
import json
from .models import ADUser, User
from .database import init_db, get_db
from .security import get_password_hash
from .schemas import UserPublic, UserCreate, UserList

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
        

@app.get("/users/", response_model=UserList)
def read_users():
    return {"users": database}

@app.post("/test-user")
def create_test_user(session: Session = Depends(get_db)):
    
    existing_user = session.query(User).filter(User.username == "test-user").first()
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Usuário 'test-user' já existe."
        )
    
    hashed_pwd = get_password_hash('123')
    
    user = UserCreate(username="test-user", email="admin@test.com", password=hashed_pwd, enabled=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserCreate, session: Session = Depends(get_db)):
    
    db_user = session.query(User).filter(User.username == user.username).first()
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Username already exists"
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Email already exists'
            )
    
    hashed_pwd = get_password_hash(user.password)
    
    db_user = User(username=user.username, email=user.email, password=hashed_pwd, enabled=True)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
    

@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(
    user: User,
    session: Session = Depends(get_db)
):
    db_user = session.scalar(select(User).where(User.username == user.username))
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    try:
        db_user.username = user.username
        db_user.password = user.password
        db_user.email = user.email
        session.commit()
        session.refresh(db_user)
    
        return db_user
    except:
        pass