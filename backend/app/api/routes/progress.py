from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.progress import (
    ISLAttemptCreate,
    ISLAttemptResponse,
    ProgressAnalyticsResponse,
    ProgressSummaryResponse,
)
from app.services.progress_service import ProgressService


router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


@router.post(
    "/isl-attempts",
    response_model=ISLAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_isl_attempt(
    payload: ISLAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Record an authenticated learner ISL attempt.

    The authenticated user's identity is authoritative.
    """

    service = ProgressService(db)

    try:
        return service.record_isl_attempt(
            user_id=current_user.id,
            target_letter=payload.target_letter,
            predicted_letter=(
                payload.predicted_letter
            ),
            confidence=payload.confidence,
            accepted=payload.accepted,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=ProgressSummaryResponse,
)
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Return basic progress for the authenticated learner.
    """

    service = ProgressService(db)

    return service.get_user_progress(
        current_user.id
    )


@router.get(
    "/me/analytics",
    response_model=ProgressAnalyticsResponse,
)
def get_my_progress_analytics(
    recent_limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum number of recent "
            "ISL attempts to return."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Return detailed analytics for the authenticated learner.

    Security boundary:
    - user_id is never accepted from the client
    - current_user.id comes from the validated JWT
    - analytics are therefore scoped to the authenticated learner
    """

    service = ProgressService(db)

    try:
        return service.get_user_analytics(
            current_user.id,
            recent_limit=recent_limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        ) from exc