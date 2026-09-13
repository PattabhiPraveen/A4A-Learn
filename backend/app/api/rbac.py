from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.models.user import User


def require_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require an authenticated active teacher.

    Authentication remains owned by get_current_user.
    Authorization is evaluated against the database-backed User
    returned by that dependency.

    Never trust a role supplied by the request body, query string,
    or frontend.
    """

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    role = (current_user.role or "").strip().lower()

    if role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required.",
        )

    return current_user
