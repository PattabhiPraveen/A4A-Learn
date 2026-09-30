from fastapi import APIRouter, Depends  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import AccessibilityProfileUpdate, UserResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def _user_response(user: User) -> UserResponse:
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


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return _user_response(current_user)


@router.patch(
    "/me/accessibility",
    response_model=UserResponse,
)
def update_my_accessibility_profile(
    profile: AccessibilityProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.accessibility_profile = profile.accessibility_profile
    current_user.preferred_language = profile.preferred_language
    current_user.isl_enabled = profile.isl_enabled
    current_user.captions_enabled = profile.captions_enabled

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return _user_response(current_user)