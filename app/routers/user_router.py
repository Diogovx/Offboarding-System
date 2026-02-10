from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from sqlalchemy import select

from app.enums import AuditAction, AuditStatus
from app.models import User
from app.schemas import (
    AuditLogCreate,
    FilterPage,
    UserCreate,
    UserList,
    UserPublic,
)
from app.security import (
    Current_user,
    Db_session,
    Editor_user,
    Token,
    get_password_hash,
)
from app.security.security import settings
from app.services import create_audit_log

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

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.LIST_USERS,
            status=AuditStatus.SUCCESS,
            message=f"""Listed users offset={filter_users.offset}
            limit={filter_users.limit}""",
            user_id=current_user.id,
            username=current_user.username,
            resource="/users",
        ),
    )

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
    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.CREATE_USER,
            status=AuditStatus.SUCCESS,
            message="Test user created",
            user_id=None,
            username="system",
            resource="test-user",
        ),
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/", status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(
    user: UserCreate,
    session: Db_session,
    current_user: Editor_user,
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
    try:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.CREATE_USER,
                status=AuditStatus.SUCCESS,
                message=f"User '{user.username}' created",
                user_id=current_user.id,
                username=current_user.username,
                resource=user.username,
            ),
        )
    except HTTPException:
        create_audit_log(
            session,
                AuditLogCreate(
                action=AuditAction.CREATE_USER,
                status=AuditStatus.FAILED,
                message="Username or email already exists",
                user_id=current_user.id,
                username=current_user.username,
                resource=user.username,
            ),
        )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.put("/{username}", response_model=UserPublic)
def update_user(
    username: str,
    user: User,
    session: Db_session,
    current_user: Editor_user
):
    db_user = session.scalar(
        select(User).where(User.username == username)
    )
    if not db_user:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.UPDATE_USER,
                status=AuditStatus.FAILED,
                message="Target user not found",
                user_id=current_user.id,
                username=current_user.username,
                resource=username,
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    db_user.username = user.username
    db_user.password = user.password
    db_user.email = user.email
    session.commit()
    session.refresh(db_user)

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.UPDATE_USER,
            status=AuditStatus.SUCCESS,
            message=f"User '{username}' updated",
            user_id=current_user.id,
            username=current_user.username,
            resource=username,
        ),
    )

    return db_user


@router.get("/me", response_model=UserPublic)
def read_users_me(
    token: Token, session: Db_session, current_user: Current_user
):
    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.READ_CURRENT_USER,
                status=AuditStatus.SUCCESS,
                message="Read own profile",
                user_id=current_user.id,
                username=current_user.username,
                resource="/users/me",
            ),
        )
    except ExpiredSignatureError:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.READ_CURRENT_USER,
                status=AuditStatus.DENIED,
                message="Invalid or expired token",
                user_id=None,
                username=None,
                resource="/users/me",
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Token has expired",
        )
    except InvalidTokenError:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.READ_CURRENT_USER,
                status=AuditStatus.DENIED,
                message="Invalid or expired token",
                user_id=None,
                username=None,
                resource="/users/me",
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = session.query(User).filter(User.username == username).first()
    if not user:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.READ_CURRENT_USER,
                status=AuditStatus.FAILED,
                message="User not found",
                user_id=None,
                username=None,
                resource="/users/me",
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return user
