import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.api.rbac import require_teacher
from app.models.user import User
from app.schemas.learning_review import (
    LearnerReviewRequest,
    LearnerReviewRequestResponse,
    LearningReviewResponse,
    TeacherReviewResolveRequest,
)
from app.services.learning_review_service import LearningReviewService


router = APIRouter(
    prefix="/reviews",
    tags=["Human Review"],
)


@router.post(
    "/request",
    response_model=LearnerReviewRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_teacher_review(
    payload: LearnerReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LearningReviewService(db)

    try:
        result = service.evaluate_and_escalate(
            student_id=current_user.id,
            activity_type=payload.activity_type,
            activity_reference_id=payload.activity_reference_id,
            question_or_activity=payload.question_or_activity,
            student_requested_help=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if result.review is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Human review could not be created.",
        )

    return LearnerReviewRequestResponse(
        decision=result.decision.value,
        reason=result.reason,
        requires_human_review=result.requires_human_review,
        review_created=result.created,
        review=result.review,
    )


@router.get(
    "/me",
    response_model=list[LearningReviewResponse],
)
def get_my_reviews(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LearningReviewService(db)

    return service.get_student_reviews(
        student_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/pending",
    response_model=list[LearningReviewResponse],
)
def get_pending_reviews(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_teacher: User = Depends(require_teacher),
):
    service = LearningReviewService(db)

    return service.get_pending_reviews(
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{review_id}",
    response_model=LearningReviewResponse,
)
def get_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(require_teacher),
):
    service = LearningReviewService(db)

    review = service.get_review(review_id=review_id)

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning review not found.",
        )

    return review


@router.patch(
    "/{review_id}/resolve",
    response_model=LearningReviewResponse,
)
def resolve_review(
    review_id: uuid.UUID,
    payload: TeacherReviewResolveRequest,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(require_teacher),
):
    service = LearningReviewService(db)

    try:
        return service.resolve_review(
            review_id=review_id,
            teacher_id=current_teacher.id,
            teacher_feedback=payload.teacher_feedback,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning review not found.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
