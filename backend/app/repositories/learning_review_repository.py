import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.learning_review import LearningReview


class LearningReviewRepository:
    """
    Persistence operations for human-in-the-loop learning reviews.

    This repository contains database operations only.
    Escalation decisions and teacher-review policies belong
    in the service/policy layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        student_id: uuid.UUID,
        activity_type: str,
        question_or_activity: str,
        reason_for_escalation: str,
        activity_reference_id: str | None = None,
        ai_response: str | None = None,
        retrieved_sources: str | None = None,
        ai_confidence: float | None = None,
        student_attempts: int | None = None,
    ) -> LearningReview:
        review = LearningReview(
            student_id=student_id,
            activity_type=activity_type,
            activity_reference_id=activity_reference_id,
            question_or_activity=question_or_activity,
            ai_response=ai_response,
            retrieved_sources=retrieved_sources,
            ai_confidence=ai_confidence,
            reason_for_escalation=reason_for_escalation,
            student_attempts=student_attempts,
            status="pending",
        )

        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)

        return review

    def get_by_id(
        self,
        review_id: uuid.UUID,
    ) -> LearningReview | None:
        stmt = select(LearningReview).where(
            LearningReview.id == review_id
        )
        return self.db.scalar(stmt)

    def list_by_student(
        self,
        student_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LearningReview]:
        stmt = (
            select(LearningReview)
            .where(LearningReview.student_id == student_id)
            .order_by(
                LearningReview.created_at.desc(),
                LearningReview.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(stmt).all())

    def list_pending(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LearningReview]:
        stmt = (
            select(LearningReview)
            .where(LearningReview.status == "pending")
            .order_by(
                LearningReview.created_at.asc(),
                LearningReview.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(stmt).all())

    def count_pending(self) -> int:
        stmt = (
            select(func.count())
            .select_from(LearningReview)
            .where(LearningReview.status == "pending")
        )

        return int(self.db.scalar(stmt) or 0)

    def count_pending_by_student(
        self,
        student_id: uuid.UUID,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(LearningReview)
            .where(
                LearningReview.student_id == student_id,
                LearningReview.status == "pending",
            )
        )

        return int(self.db.scalar(stmt) or 0)

    def find_pending_for_activity(
        self,
        *,
        student_id: uuid.UUID,
        activity_type: str,
        activity_reference_id: str,
    ) -> LearningReview | None:
        """
        Finds an existing pending review for the same learner
        and activity reference.

        The service layer can use this to avoid creating duplicate
        teacher-review requests.
        """
        stmt = (
            select(LearningReview)
            .where(
                LearningReview.student_id == student_id,
                LearningReview.activity_type == activity_type,
                LearningReview.activity_reference_id
                == activity_reference_id,
                LearningReview.status == "pending",
            )
            .order_by(
                LearningReview.created_at.desc(),
                LearningReview.id.desc(),
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def save(
        self,
        review: LearningReview,
    ) -> LearningReview:
        """
        Flushes changes made to an existing review.

        Transaction ownership remains with the service layer.
        """
        self.db.add(review)
        self.db.flush()
        self.db.refresh(review)

        return review
