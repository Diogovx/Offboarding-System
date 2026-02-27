from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError, decode
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


def require_admin(user: User = Depends(get_current_user)):
    admin_role = 1
    if user.userRole != admin_role:
        raise HTTPException(
            status_code=403, detail="Admin privileges required"
        )
    return user


def require_editor(user: User = Depends(get_current_user)):
    editor_role = 2
    if user.userRole > editor_role:
        raise HTTPException(
            status_code=403, detail="Editor privileges required"
        )
    return user


Current_user = Annotated[User, Depends(get_current_user)]
Admin_user = Annotated[User, Depends(require_admin)]
Token = Annotated[str, Depends(oauth2_scheme)]
Editor_user = Annotated[User, Depends(require_editor)]
Form_data = Annotated[OAuth2PasswordRequestForm, Depends()]
