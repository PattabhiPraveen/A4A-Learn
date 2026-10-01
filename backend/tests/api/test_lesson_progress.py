from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.services.assessment_content_service import (
    AssessmentContentService,
)


TEST_PASSWORD = "A4A_Lesson_Progress_Test_2026!"


def _register_and_login(
    client: TestClient,
):
    email = (
        f"lesson-progress-{uuid.uuid4().hex}"
        "@example.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Lesson Progress Test Student",
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200

    payload = login.json()

    assert "access_token" in payload

    return {
        "Authorization": (
            f"Bearer {payload['access_token']}"
        )
    }


def _build_submission(
    lesson_id: str,
    correct_count: int,
):
    service = AssessmentContentService()

    assessment = service.get_assessment(
        lesson_id
    )

    answer_key = service.get_answer_key(
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
            {
                "question_id": question.id,
                "selected_option": (
                    selected_option
                ),
            }
        )

    return {
        "answers": answers,
    }


def test_lesson_progress_tracks_latest_and_best_attempt(
    client,
):
    headers = _register_and_login(client)

    # -------------------------------------------------
    # First assessment attempt: 80%
    # -------------------------------------------------

    first_submission = _build_submission(
        "lesson_01",
        correct_count=4,
    )

    first_response = client.post(
        "/assessments/lessons/lesson_01/submit",
        headers=headers,
        json=first_submission,
    )

    assert first_response.status_code == 201

    first_payload = first_response.json()

    assert first_payload["lesson_id"] == "lesson_01"
    assert first_payload["curriculum_id"] == "PY-01"
    assert first_payload["correct_answers"] == 4
    assert first_payload["total_questions"] == 5
    assert first_payload["score_percent"] == 80
    assert first_payload["recommendation"] == "continue"

    # -------------------------------------------------
    # Progress after first attempt
    # -------------------------------------------------

    progress_response = client.get(
        "/progress/lessons/lesson_01",
        headers=headers,
    )

    assert progress_response.status_code == 200

    progress = progress_response.json()

    assert progress["lesson_id"] == "lesson_01"
    assert progress["curriculum_id"] == "PY-01"

    assert progress["assessment_attempts"] == 1

    assert progress["latest_score_percent"] == 80
    assert progress["latest_recommendation"] == "continue"

    assert progress["best_score_percent"] == 80

    assert progress["completed"] is True

    assert progress["latest_attempt_at"] is not None

    # -------------------------------------------------
    # Second assessment attempt: 60%
    # -------------------------------------------------

    second_submission = _build_submission(
        "lesson_01",
        correct_count=3,
    )

    second_response = client.post(
        "/assessments/lessons/lesson_01/submit",
        headers=headers,
        json=second_submission,
    )

    assert second_response.status_code == 201

    second_payload = second_response.json()

    assert second_payload["lesson_id"] == "lesson_01"
    assert second_payload["curriculum_id"] == "PY-01"
    assert second_payload["correct_answers"] == 3
    assert second_payload["total_questions"] == 5
    assert second_payload["score_percent"] == 60
    assert second_payload["recommendation"] == "practice"

    # -------------------------------------------------
    # Progress after second attempt
    # -------------------------------------------------

    progress_response = client.get(
        "/progress/lessons/lesson_01",
        headers=headers,
    )

    assert progress_response.status_code == 200

    progress = progress_response.json()

    assert progress["lesson_id"] == "lesson_01"
    assert progress["curriculum_id"] == "PY-01"

    # Two persisted assessment attempts.
    assert progress["assessment_attempts"] == 2

    # Latest attempt is 60%.
    assert progress["latest_score_percent"] == 60
    assert progress["latest_recommendation"] == "practice"

    # Historical best remains 80%.
    assert progress["best_score_percent"] == 80

    assert progress["completed"] is True

    assert progress["latest_attempt_at"] is not None


def test_lesson_progress_requires_authentication(
    client,
):
    response = client.get(
        "/progress/lessons/lesson_01"
    )

    assert response.status_code == 401


def test_lesson_progress_has_no_user_id_parameter(
    client,
):
    response = client.get(
        "/progress/lessons/lesson_01?user_id=some-other-user"
    )

    # Authentication is required before any
    # learner-specific progress can be returned.
    assert response.status_code == 401