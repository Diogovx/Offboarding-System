from fastapi import HTTPException,  Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer
from http import HTTPStatus
from sqlalchemy import select
from sqlalchemy.orm import Session
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from app.models import User
from app.schemas import UserPublic
from app.database import get_db
from app.security import get_password_hash, SECRET_KEY, ALGORITHM, get_current_user, require_admin
from app.schemas import UserCreate, UserList

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/", response_model=UserList)
def list_users(session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = session.query(User).all()
    return {"users": users}

@router.post("/test", response_model=UserPublic)
def create_test_user(session: Session = Depends(get_db)):
    existing_user = session.query(User).filter(User.username == "test-user").first()
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="'test-user' already exists."
        )

    hashed_pwd = get_password_hash('123')
    user = User(username="test-user", email="admin@test.com", password=hashed_pwd, enabled=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserCreate, session: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    
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
    
    db_user = User(username=user.username, email=user.email, password=hashed_pwd, enabled=True, userRole=user.userRole)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
    

@router.put('/{user_id}', response_model=UserPublic)
def update_user(
    user: User,
    session: Session = Depends(get_db)
):
    db_user = session.scalar(select(User).where(User.username == user.username))
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    
    db_user.username = user.username
    db_user.password = user.password
    db_user.email = user.email
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/me", response_model=UserPublic)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid authentication token",
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Token has expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")

    return user