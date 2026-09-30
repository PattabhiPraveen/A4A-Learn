from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.learning import (
    LearningLessonDetail,
    LearningLessonSummary,
)
from app.services.learning_content_service import (
    LearningContentNotFoundError,
    LearningContentService,
)


router = APIRouter(
    prefix="/learning",
    tags=["Learning"],
)

learning_content_service = LearningContentService()


@router.get(
    "/lessons",
    response_model=list[LearningLessonSummary],
    status_code=status.HTTP_200_OK,
)
def list_lessons(
    current_user: User = Depends(
        get_current_user
    ),
) -> list[LearningLessonSummary]:
    """
    Return approved learner-facing lessons.

    Authentication is required.

    Only governed DS001 MVP learning content is exposed
    by LearningContentService.
    """
    return learning_content_service.list_lessons()


@router.get(
    "/lessons/{lesson_id}",
    response_model=LearningLessonDetail,
    status_code=status.HTTP_200_OK,
)
def get_lesson(
    lesson_id: str,
    current_user: User = Depends(
        get_current_user
    ),
) -> LearningLessonDetail:
    """
    Return one approved learner-facing lesson.
    """
    try:
        return learning_content_service.get_lesson(
            lesson_id
        )

    except LearningContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning lesson not found.",
        ) from exc