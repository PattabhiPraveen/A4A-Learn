from fastapi import APIRouter, Depends, HTTPException, status  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.api.dependencies import get_db
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import (
    create_user,
    get_user_by_email,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new learner account.

    Security boundary:
    - Public registration creates a student account only.
    - Role is assigned by the backend service.
    - Accessibility preferences are not inferred during registration.
    """

    existing_user = get_user_by_email(
        db,
        user_data.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = create_user(
        db=db,
        full_name=user_data.full_name,
        email=user_data.email,
        password=user_data.password,
    )

    return UserResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        accessibility_profile=user.accessibility_profile,
        preferred_language=user.preferred_language,
        isl_enabled=user.isl_enabled,
        captions_enabled=user.captions_enabled,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate an existing user and issue a JWT access token.

    Authorization information remains role-based.
    Accessibility preferences are retrieved separately through /users/me
    and are not used for authorization.
    """

    user = get_user_by_email(
        db,
        login_data.email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )