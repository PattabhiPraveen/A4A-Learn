from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.schemas.assessment import (
    AssessmentAnswerSubmission,
    LessonAssessmentSubmission,
)
from app.services.assessment_content_service import (
    AssessmentContentService,
)
from app.services.assessment_service import (
    AssessmentService,
    AssessmentSubmissionError,
)


class FakeAttempt:
    def __init__(
        self,
        *,
        user_id,
        lesson_id,
        curriculum_id,
        correct_answers,
        total_questions,
        score_percent,
        recommendation,
    ):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.lesson_id = lesson_id
        self.curriculum_id = curriculum_id
        self.correct_answers = correct_answers
        self.total_questions = total_questions
        self.score_percent = score_percent
        self.recommendation = recommendation
        self.created_at = datetime.now(timezone.utc)


class FakeRepository:
    def __init__(self):
        self.created = []

    def create(self, **kwargs):
        attempt = FakeAttempt(**kwargs)
        self.created.append(attempt)
        return attempt


def build_service():
    service = AssessmentService(
        db=None,
        content_service=AssessmentContentService(),
    )

    repository = FakeRepository()
    service.repository = repository

    return service, repository


def build_submission(
    lesson_id: str,
    correct_count: int,
):
    content = AssessmentContentService()

    assessment = content.get_assessment(
        lesson_id
    )

    answer_key = content.get_answer_key(
        lesson_id
    )

    answers = []

    for index, question in enumerate(
        assessment.questions
    ):
        correct_option = answer_key[
            question.id
        ]

        if index < correct_count:
            selected_option = correct_option
        else:
            selected_option = (
                correct_option + 1
            ) % len(question.options)

        answers.append(
            AssessmentAnswerSubmission(
                question_id=question.id,
                selected_option=selected_option,
            )
        )

    return LessonAssessmentSubmission(
        answers=answers
    )


@pytest.mark.parametrize(
    (
        "correct_count",
        "expected_score",
        "expected_recommendation",
    ),
    [
        (0, 0, "review"),
        (1, 20, "review"),
        (2, 40, "review"),
        (3, 60, "practice"),
        (4, 80, "continue"),
        (5, 100, "continue"),
    ],
)
def test_deterministic_scoring(
    correct_count,
    expected_score,
    expected_recommendation,
):
    service, repository = build_service()

    user_id = uuid.uuid4()

    result = service.submit(
        user_id=user_id,
        lesson_id="lesson_01",
        submission=build_submission(
            "lesson_01",
            correct_count,
        ),
    )

    assert result.correct_answers == correct_count
    assert result.total_questions == 5
    assert result.score_percent == expected_score
    assert (
        result.recommendation
        == expected_recommendation
    )

    assert len(result.question_results) == 5
    assert len(repository.created) == 1

    persisted = repository.created[0]

    assert persisted.user_id == user_id
    assert persisted.score_percent == expected_score
    assert (
        persisted.recommendation
        == expected_recommendation
    )


def test_duplicate_question_ids_rejected():
    service, repository = build_service()

    submission = build_submission(
        "lesson_01",
        5,
    )

    submission.answers[1].question_id = (
        submission.answers[0].question_id
    )

    with pytest.raises(
        AssessmentSubmissionError,
        match="Duplicate question IDs",
    ):
        service.submit(
            user_id=uuid.uuid4(),
            lesson_id="lesson_01",
            submission=submission,
        )

    assert repository.created == []


def test_missing_answer_rejected():
    service, repository = build_service()

    submission = build_submission(
        "lesson_01",
        5,
    )

    submission.answers.pop()

    with pytest.raises(
        AssessmentSubmissionError,
        match="Exactly five answers",
    ):
        service.submit(
            user_id=uuid.uuid4(),
            lesson_id="lesson_01",
            submission=submission,
        )

    assert repository.created == []


def test_unknown_question_id_rejected():
    service, repository = build_service()

    submission = build_submission(
        "lesson_01",
        5,
    )

    submission.answers[0].question_id = (
        "UNKNOWN-Q"
    )

    with pytest.raises(
        AssessmentSubmissionError,
        match="do not match",
    ):
        service.submit(
            user_id=uuid.uuid4(),
            lesson_id="lesson_01",
            submission=submission,
        )

    assert repository.created == []


def test_out_of_range_option_rejected():
    service, repository = build_service()

    submission = build_submission(
        "lesson_01",
        5,
    )

    submission.answers[0].selected_option = 4

    with pytest.raises(
        AssessmentSubmissionError,
        match="outside the valid range",
    ):
        service.submit(
            user_id=uuid.uuid4(),
            lesson_id="lesson_01",
            submission=submission,
        )

    assert repository.created == []


def test_question_results_do_not_expose_answer_key():
    service, _ = build_service()

    result = service.submit(
        user_id=uuid.uuid4(),
        lesson_id="lesson_01",
        submission=build_submission(
            "lesson_01",
            5,
        ),
    )

    payload = result.model_dump()

    for question_result in payload[
        "question_results"
    ]:
        assert (
            "correct_option"
            not in question_result
        )