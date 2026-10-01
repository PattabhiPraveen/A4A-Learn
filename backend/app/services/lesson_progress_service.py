from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.lesson_progress_repository import (
    LessonProgressRepository,
)
from app.schemas.lesson_progress import (
    LessonProgressResponse,
)


class LessonProgressService:
    """
    Business service for learner progress on a governed lesson.

    Assessment correctness and recommendations are produced
    by AssessmentService.

    This service aggregates persisted assessment evidence
    for the authenticated learner.
    """

    def __init__(self, db: Session) -> None:
        self.repository = LessonProgressRepository(db)

    def get_lesson_progress(
        self,
        *,
        user_id: UUID,
        lesson_id: str,
    ) -> LessonProgressResponse:
        """
        Return progress for one authenticated learner
        and lesson.
        """

        attempts = (
            self.repository.list_by_user_and_lesson(
                user_id=user_id,
                lesson_id=lesson_id,
            )
        )

        if not attempts:
            return LessonProgressResponse(
                lesson_id=lesson_id,
                curriculum_id="",
                assessment_attempts=0,
                latest_score_percent=None,
                latest_recommendation=None,
                best_score_percent=None,
                completed=False,
                latest_attempt_at=None,
            )

        latest = attempts[0]

        best_score = max(
            attempt.score_percent
            for attempt in attempts
        )

        return LessonProgressResponse(
            lesson_id=lesson_id,
            curriculum_id=latest.curriculum_id,
            assessment_attempts=len(attempts),
            latest_score_percent=latest.score_percent,
            latest_recommendation=latest.recommendation,
            best_score_percent=best_score,
            completed=True,
            latest_attempt_at=latest.created_at,
        )