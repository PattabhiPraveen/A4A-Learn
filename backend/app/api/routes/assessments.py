from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.assessment import (
    LessonAssessmentResponse,
    LessonAssessmentResultResponse,
    LessonAssessmentSubmission,
)
from app.services.assessment_content_service import (
    AssessmentContentNotFoundError,
    AssessmentContentService,
    AssessmentContentValidationError,
)
from app.services.assessment_service import (
    AssessmentService,
    AssessmentSubmissionError,
)


router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"],
)


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonAssessmentResponse,
    status_code=status.HTTP_200_OK,
)
def get_lesson_assessment(
    lesson_id: str,
    current_user: User = Depends(
        get_current_user
    ),
) -> LessonAssessmentResponse:
    """
    Return a governed learner-safe lesson assessment.

    Authentication is required.

    The learner receives:
    - question ID
    - question text
    - answer options

    The correct answer key is intentionally excluded.
    """

    # Authentication is intentionally required even though
    # learner identity is not otherwise needed for a GET.
    _ = current_user

    service = AssessmentContentService()

    try:
        return service.get_assessment(
            lesson_id
        )

    except AssessmentContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AssessmentContentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Governed assessment content is invalid."
            ),
        ) from exc


@router.post(
    "/lessons/{lesson_id}/submit",
    response_model=LessonAssessmentResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_lesson_assessment(
    lesson_id: str,
    submission: LessonAssessmentSubmission,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        get_current_user
    ),
) -> LessonAssessmentResultResponse:
    """
    Score and persist an authenticated learner assessment.

    Security and trust boundaries:
    - authenticated user ID comes from the JWT
    - answer key remains server-side
    - correctness is calculated server-side
    - score is calculated server-side
    - recommendation is calculated server-side
    - result is persisted by the backend
    """

    service = AssessmentService(
        db=db
    )

    try:
        return service.submit(
            user_id=current_user.id,
            lesson_id=lesson_id,
            submission=submission,
        )

    except AssessmentContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AssessmentSubmissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except AssessmentContentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Governed assessment content is invalid."
            ),
        ) from exc