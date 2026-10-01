from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LessonProgressResponse(BaseModel):
    """
    Learner-safe progress for one governed lesson.

    Assessment correctness is calculated server-side.
    This response exposes progress facts and the latest
    governed recommendation only.
    """

    lesson_id: str
    curriculum_id: str

    assessment_attempts: int

    latest_score_percent: int | None
    latest_recommendation: str | None

    best_score_percent: int | None

    completed: bool

    latest_attempt_at: datetime | None