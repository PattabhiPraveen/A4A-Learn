from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.isl_content import (
    ISLLessonManifest,
)
from app.schemas.learning import (
    LearningLessonDetail,
    LearningLessonSummary,
)
from app.services.isl_content_service import (
    ISLContentNotFoundError,
    ISLContentService,
    ISLContentValidationError,
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
isl_content_service = ISLContentService()


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
    "/lessons/{lesson_id}/isl",
    response_model=ISLLessonManifest,
    status_code=status.HTTP_200_OK,
)
def get_lesson_isl_content(
    lesson_id: str,
    current_user: User = Depends(
        get_current_user
    ),
) -> ISLLessonManifest:
    """
    Return governed ISL learning content for one lesson.

    The requested lesson must first exist in the approved
    DS001 curriculum.

    ISL learning content is then resolved independently
    from the governed DS003 ISL learning registry.

    This endpoint never generates or invents ISL signs.
    Only content registered through the governed ISL
    content service may be returned.
    """
    try:
        lesson = (
            learning_content_service.get_lesson(
                lesson_id
            )
        )

        manifest = (
            isl_content_service.get_manifest(
                lesson.id
            )
        )

        if (
            manifest.curriculum_id
            != lesson.curriculum_id
        ):
            raise ISLContentValidationError(
                "ISL curriculum identifier does "
                "not match the governed lesson."
            )

        if manifest.title != lesson.title:
            raise ISLContentValidationError(
                "ISL lesson title does not match "
                "the governed lesson."
            )

        return manifest

    except LearningContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning lesson not found.",
        ) from exc

    except ISLContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "ISL learning content is not "
                "registered for this lesson."
            ),
        ) from exc

    except ISLContentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Governed ISL learning content "
                "failed validation."
            ),
        ) from exc


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