from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.models.user_model import User
from app.security import (
    Db_session,
    Form_data,
    create_access_token,
    verify_password,
)

router = APIRouter()


@router.post("/token")
def login(
    db: Db_session,
    form_data: Form_data,
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
