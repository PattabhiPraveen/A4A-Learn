import uuid

from app.services.learning_content_service import (
    LearningContentNotFoundError,
)


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_student_with_token(
    client,
):
    email = (
        f"rag_lesson_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    password = "A4A_Test_2026!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": (
                "RAG Lesson Test Student"
            ),
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201, (
        register_response.text
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, (
        login_response.text
    )

    return login_response.json()[
        "access_token"
    ]


def grounded_result(
    question: str,
    *,
    source: str,
) -> dict:
    return {
        "question": question,
        "answer": (
            "A variable stores a value "
            "in Python. [Source 1]"
        ),
        "grounded": True,
        "sources": [
            {
                "title": (
                    "Python Variables"
                ),
                "source": source,
                "distance": 0.0,
                "source_type": (
                    "curriculum"
                ),
            },
        ],
    }


def test_question_only_preserves_original_rag_call(
    client,
    monkeypatch,
):
    token = create_student_with_token(
        client
    )

    calls = []

    def fake_answer(question: str):
        calls.append(question)

        return grounded_result(
            question,
            source="curriculum",
        )

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "What is a variable?"
            ),
        },
    )

    assert response.status_code == 200

    assert calls == [
        "What is a variable?"
    ]

    body = response.json()

    assert body["grounded"] is True

    assert (
        body["requires_human_review"]
        is False
    )


def test_lesson_id_reaches_rag_service(
    client,
    monkeypatch,
):
    token = create_student_with_token(
        client
    )

    calls = []

    def fake_answer(
        question: str,
        *,
        lesson_id: str | None = None,
    ):
        calls.append(
            (question, lesson_id)
        )

        return grounded_result(
            question,
            source=lesson_id or "curriculum",
        )

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "What is a variable?"
            ),
            "lesson_id": "lesson_01",
        },
    )

    assert response.status_code == 200

    assert calls == [
        (
            "What is a variable?",
            "lesson_01",
        )
    ]

    body = response.json()

    assert body["grounded"] is True

    assert (
        body["sources"][0]["source"]
        == "lesson_01"
    )

    assert (
        body["sources"][0]["source_type"]
        == "curriculum"
    )


def test_unknown_lesson_returns_404(
    client,
    monkeypatch,
):
    token = create_student_with_token(
        client
    )

    def fake_answer(
        question: str,
        *,
        lesson_id: str | None = None,
    ):
        raise LearningContentNotFoundError(
            (
                "Learning lesson "
                f"'{lesson_id}' was not found."
            )
        )

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Explain this lesson."
            ),
            "lesson_id": (
                "lesson_9999"
            ),
        },
    )

    assert response.status_code == 404

    assert (
        "lesson_9999"
        in response.json()["detail"]
    )