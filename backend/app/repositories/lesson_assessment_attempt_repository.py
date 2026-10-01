from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_assessment_attempt import (
    LessonAssessmentAttempt,
)


class LessonAssessmentAttemptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        lesson_id: str,
        curriculum_id: str,
        correct_answers: int,
        total_questions: int,
        score_percent: int,
        recommendation: str,
    ) -> LessonAssessmentAttempt:
        attempt = LessonAssessmentAttempt(
            user_id=user_id,
            lesson_id=lesson_id,
            curriculum_id=curriculum_id,
            correct_answers=correct_answers,
            total_questions=total_questions,
            score_percent=score_percent,
            recommendation=recommendation,
        )

        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def list_for_user(
        self,
        user_id: UUID,
    ) -> list[LessonAssessmentAttempt]:
        statement = (
            select(LessonAssessmentAttempt)
            .where(
                LessonAssessmentAttempt.user_id == user_id
            )
            .order_by(
                LessonAssessmentAttempt.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )