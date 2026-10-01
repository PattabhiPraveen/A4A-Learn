from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_assessment_attempt import (
    LessonAssessmentAttempt,
)


class LessonProgressRepository:
    """
    Repository for learner lesson-assessment progress.

    Reads the existing lesson_assessment_attempts table.
    No additional persistence table is required.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user_and_lesson(
        self,
        *,
        user_id: UUID,
        lesson_id: str,
    ) -> list[LessonAssessmentAttempt]:
        """
        Return all assessment attempts for one learner
        and lesson, newest first.
        """

        statement = (
            select(LessonAssessmentAttempt)
            .where(
                LessonAssessmentAttempt.user_id == user_id,
                LessonAssessmentAttempt.lesson_id == lesson_id,
            )
            .order_by(
                LessonAssessmentAttempt.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )