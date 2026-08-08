from collections.abc import Generator

from fastapi import Depends, HTTPException, status  # type: ignore[import]
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # type: ignore[import]
from jose.exceptions import JWTError  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.core.security import decode_access_token
from app.database.database import SessionLocal
from app.models.user import User
# from app.services.user_service import get_user_by_email


security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user