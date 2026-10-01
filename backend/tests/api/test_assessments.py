from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.services.assessment_content_service import (
    AssessmentContentService,
)


TEST_PASSWORD = "A4A_Assessment_Test_2026!"


def _register_and_login(
    client: TestClient,
):
    email = (
        f"assessment-{uuid.uuid4().hex}"
        "@example.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Assessment Test Student",
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


def test_assessment_requires_authentication(
    client,
):
    response = client.get(
        "/assessments/lessons/lesson_01"
    )

    assert response.status_code == 401


def test_authenticated_assessment_is_learner_safe(
    client,
):
    headers = _register_and_login(client)

    response = client.get(
        "/assessments/lessons/lesson_01",
        headers=headers,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["lesson_id"] == "lesson_01"
    assert payload["curriculum_id"] == "PY-01"
    assert len(payload["questions"]) == 5

    for question in payload["questions"]:
        assert "id" in question
        assert "question" in question
        assert "options" in question

        # Server answer key must never be
        # exposed to the learner.
        assert "correct_option" not in question


def test_all_showcase_assessments_available(
    client,
):
    headers = _register_and_login(client)

    for number in range(1, 7):
        lesson_id = f"lesson_{number:02d}"

        response = client.get(
            f"/assessments/lessons/{lesson_id}",
            headers=headers,
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["lesson_id"] == lesson_id
        assert len(payload["questions"]) == 5

        for question in payload["questions"]:
            assert "correct_option" not in question


def test_assessment_submission_80_percent(
    client,
):
    headers = _register_and_login(client)

    submission = _build_submission(
        "lesson_01",
        correct_count=4,
    )

    response = client.post(
        "/assessments/lessons/lesson_01/submit",
        headers=headers,
        json=submission,
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["lesson_id"] == "lesson_01"
    assert payload["curriculum_id"] == "PY-01"

    assert payload["correct_answers"] == 4
    assert payload["total_questions"] == 5
    assert payload["score_percent"] == 80
    assert payload["recommendation"] == "continue"

    assert len(
        payload["question_results"]
    ) == 5

    assert sum(
        1
        for result in payload["question_results"]
        if result["is_correct"]
    ) == 4

    # Correct answer must not be returned
    # to the learner.
    for result in payload[
        "question_results"
    ]:
        assert "correct_option" not in result


def test_assessment_submission_60_percent(
    client,
):
    headers = _register_and_login(client)

    submission = _build_submission(
        "lesson_01",
        correct_count=3,
    )

    response = client.post(
        "/assessments/lessons/lesson_01/submit",
        headers=headers,
        json=submission,
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["correct_answers"] == 3
    assert payload["total_questions"] == 5
    assert payload["score_percent"] == 60
    assert payload["recommendation"] == "practice"


def test_assessment_submission_zero_percent(
    client,
):
    headers = _register_and_login(client)

    submission = _build_submission(
        "lesson_01",
        correct_count=0,
    )

    response = client.post(
        "/assessments/lessons/lesson_01/submit",
        headers=headers,
        json=submission,
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["correct_answers"] == 0
    assert payload["total_questions"] == 5
    assert payload["score_percent"] == 0
    assert payload["recommendation"] == "review"