from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.lesson_progress_service import (
    LessonProgressService,
)


def test_lesson_progress_returns_empty_progress_when_no_attempts(
    monkeypatch,
):
    user_id = uuid4()
    lesson_id = "lesson_01"

    class FakeRepository:
        def __init__(self, db):
            self.db = db

        def list_by_user_and_lesson(
            self,
            *,
            user_id,
            lesson_id,
        ):
            assert user_id == user_id
            assert lesson_id == lesson_id
            return []

    monkeypatch.setattr(
        "app.services.lesson_progress_service."
        "LessonProgressRepository",
        FakeRepository,
    )

    service = LessonProgressService(db=object())

    result = service.get_lesson_progress(
        user_id=user_id,
        lesson_id=lesson_id,
    )

    assert result.lesson_id == lesson_id
    assert result.curriculum_id == ""
    assert result.assessment_attempts == 0
    assert result.latest_score_percent is None
    assert result.latest_recommendation is None
    assert result.best_score_percent is None
    assert result.completed is False
    assert result.latest_attempt_at is None


def test_lesson_progress_aggregates_multiple_attempts(
    monkeypatch,
):
    user_id = uuid4()
    lesson_id = "lesson_01"

    latest_attempt_time = datetime(
        2026,
        10,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    attempts = [
        SimpleNamespace(
            lesson_id=lesson_id,
            curriculum_id="PY-01",
            score_percent=80,
            recommendation="continue",
            created_at=latest_attempt_time,
        ),
        SimpleNamespace(
            lesson_id=lesson_id,
            curriculum_id="PY-01",
            score_percent=70,
            recommendation="practice",
            created_at=datetime(
                2026,
                10,
                1,
                11,
                0,
                tzinfo=timezone.utc,
            ),
        ),
        SimpleNamespace(
            lesson_id=lesson_id,
            curriculum_id="PY-01",
            score_percent=60,
            recommendation="practice",
            created_at=datetime(
                2026,
                10,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    ]

    class FakeRepository:
        def __init__(self, db):
            self.db = db

        def list_by_user_and_lesson(
            self,
            *,
            user_id,
            lesson_id,
        ):
            assert user_id == user_id
            assert lesson_id == lesson_id
            return attempts

    monkeypatch.setattr(
        "app.services.lesson_progress_service."
        "LessonProgressRepository",
        FakeRepository,
    )

    service = LessonProgressService(db=object())

    result = service.get_lesson_progress(
        user_id=user_id,
        lesson_id=lesson_id,
    )

    assert result.lesson_id == lesson_id
    assert result.curriculum_id == "PY-01"

    assert result.assessment_attempts == 3

    # Repository returns newest attempt first.
    assert result.latest_score_percent == 80
    assert result.latest_recommendation == "continue"
    assert result.latest_attempt_at == latest_attempt_time

    # Best score across all attempts.
    assert result.best_score_percent == 80

    assert result.completed is True