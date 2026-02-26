from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Request

from app.database import Db_session
from app.enums import AuditAction, AuditStatus
from app.models.user_model import User
from app.schemas import AuditLogCreate
from app.security import (
    Current_user,
    Form_data,
    create_access_token,
    verify_password,
)
from app.services import create_audit_log

router = APIRouter()


@router.post("/token")
def login(
    db: Db_session,
    request: Request,
    form_data: Form_data,
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SYSTEM_LOGIN,
                status=AuditStatus.FAILED,
                message="Invalid credentials",
                user_id=user.id if user else None,
                username=form_data.username,
                resource="/auth/token",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials"
        )

    create_audit_log(
            db,
            AuditLogCreate(
                action=AuditAction.SYSTEM_LOGIN,
                status=AuditStatus.SUCCESS,
                message="User logged in successfully",
                user_id=user.id if user else None,
                username=form_data.username,
                resource="/auth/token",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )

    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    db: Db_session,
    request: Request,
    session: Current_user,
):
    create_audit_log(
        db,
        AuditLogCreate(
            action=AuditAction.SYSTEM_LOGOUT,
            status=AuditStatus.SUCCESS,
            message="User logged out",
            user_id=session.id,
            username=session.username,
            resource="/auth/logout",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return {"detail": "Logged out successfully"}
