from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from sqlalchemy import select

from app.models import User
from app.schemas import FilterPage, UserCreate, UserList, UserPublic
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    Admin_user,
    Current_user,
    Db_session,
    Token,
    get_password_hash,
)

router = APIRouter(prefix="/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/", response_model=UserList)
def list_users(
    session: Db_session,
    current_user: Current_user,
    filter_users: Annotated[FilterPage, Query()]
):
    users = session.scalars(
        select(User).offset(filter_users.offset).limit(filter_users.limit)
    ).all()
    return {"users": users}


@router.post("/test", response_model=UserPublic)
def create_test_user(session: Db_session):
    existing_user = (
        session.query(User).filter(User.username == "test-user").first()
    )
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="'test-user' already exists.",
        )

    hashed_pwd = get_password_hash("123")
    user = User(
        username="test-user",
        email="admin@test.com",
        password=hashed_pwd,
        enabled=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/", status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(
    user: UserCreate,
    session: Db_session,
    current_user: Admin_user,
):

    db_user = (
        session.query(User).filter(User.username == user.username).first()
    )
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Username already exists",
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="Email already exists"
            )

    hashed_pwd = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_pwd,
        enabled=True,
        userRole=user.userRole,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.put("/{username}", response_model=UserPublic)
def update_user(username: str, user: User, session: Db_session):
    db_user = session.scalar(
        select(User).where(User.username == username)
    )
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    db_user.username = user.username
    db_user.password = user.password
    db_user.email = user.email
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/me", response_model=UserPublic)
def read_users_me(
    token: Token, db: Db_session
):
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
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return user
