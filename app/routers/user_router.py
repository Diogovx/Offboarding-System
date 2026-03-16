from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from sqlalchemy import select
from uuid import UUID
from app.database import Db_session
from app.enums import AuditAction, AuditStatus
from app.models import User
from app.schemas import (
    AuditLogCreate,
    FilterPage,
    UserCreate,
    UserUpdate,
    UserList,
    UserPublic,
)
from app.security import (
    Current_user,
    Editor_user,
    Token,
    get_password_hash,
)
from app.config import settings
from app.services import create_audit_log

router = APIRouter(prefix="/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/", response_model=UserList)
def list_users(
    session: Db_session,
    current_user: Current_user,
    filter_users: Annotated[FilterPage, Query()],
    request: Request
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
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return {"users": users}


@router.post("/test", response_model=UserPublic)
def create_test_user(session: Db_session, request: Request):
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
    )  # type: ignore[call-arg]

    session.add(user)
    session.commit()
    session.refresh(user)

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.CREATE_USER,
            status=AuditStatus.SUCCESS,
            message="Test user created",
            user_id=None,
            username="system",
            resource="test-user",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )
    return user


@router.post("/", status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(
    user: UserCreate,
    session: Db_session,
    current_user: Editor_user,
    request: Request
):

    existing_username = session.scalar(
        select(User).where(User.username == user.username)
    )
    if existing_username:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Username already exists",
        )

    existing_email = session.scalar(
        select(User).where(User.email == user.email)
    )
    if existing_email:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Email already exists",
        )

    hashed_pwd = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        password=hashed_pwd,
        enabled=user.enabled,
        userRole=user.userRole,
    )  # type: ignore[call-arg]
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
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
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
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.put("/{user_id}", response_model=UserPublic)
def update_user(
    user_id: UUID,
    user: UserUpdate,
    session: Db_session,
    current_user: Editor_user,
    request: Request
):
    db_user = session.get(User, user_id)
    if not db_user:
        create_audit_log(
            session,
            AuditLogCreate(
                action=AuditAction.UPDATE_USER,
                status=AuditStatus.FAILED,
                message="Target user not found",
                user_id=current_user.id,
                username=current_user.username,
                resource=str(user_id),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )
    if user.username and user.username != db_user.username:
        check = session.scalar(
            select(User).where(User.username == user.username)
        )
        if check:
            raise HTTPException(
                status_code=409,
                detail="Username already taken"
            )
    if user.email and user.email != db_user.email:
        existing_email = session.scalar(
            select(User).where(User.email == user.email)
        )
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already taken")

    update_data = user.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "password" and value:
            setattr(db_user, field, get_password_hash(value))
        else:
            setattr(db_user, field, value)
    try:
        session.commit()
        session.refresh(db_user)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error during update: {e}"
        )

    create_audit_log(
        session,
        AuditLogCreate(
            action=AuditAction.UPDATE_USER,
            status=AuditStatus.SUCCESS,
            message=f"User '{db_user.username}'"
            f" updated by {current_user.username}",
            user_id=current_user.id,
            username=current_user.username,
            resource=db_user.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return db_user


@router.get("/me", response_model=UserPublic)
def read_users_me(
    token: Token,
    session: Db_session,
    current_user: Current_user,
    request: Request
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
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
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
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
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
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return user
