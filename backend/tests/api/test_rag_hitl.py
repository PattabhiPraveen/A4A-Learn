import uuid

from app.database.database import SessionLocal
from app.models.learning_review import LearningReview


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_student_with_token(
    client,
    *,
    full_name: str = "RAG HITL Test Student",
):
    email = (
        f"rag_hitl_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    password = "A4A_Test_2026!"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": full_name,
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

    token = login_response.json()["access_token"]

    return (
        register_response.json(),
        email,
        token,
    )


def get_pending_rag_reviews_for_student(
    student_id: str,
):
    db = SessionLocal()

    try:
        return (
            db.query(LearningReview)
            .filter(
                LearningReview.student_id
                == uuid.UUID(student_id),
                LearningReview.activity_type
                == "rag",
                LearningReview.status
                == "pending",
            )
            .all()
        )

    finally:
        db.close()


def test_rag_requires_authentication(
    client,
):
    response = client.post(
        "/rag/ask",
        json={
            "question": (
                "What is photosynthesis?"
            ),
        },
    )

    assert response.status_code == 401


def test_grounded_rag_answer_continues_without_review(
    client,
    monkeypatch,
):
    student, _, token = (
        create_student_with_token(
            client
        )
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": (
                "Photosynthesis is the process "
                "by which plants convert light "
                "energy into chemical energy."
            ),
            "grounded": True,
            "sources": [
                {
                    "title": (
                        "Photosynthesis Lesson"
                    ),
                    "source": (
                        "education/photosynthesis.md"
                    ),
                    "distance": 0.21,
                },
            ],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "What is photosynthesis?"
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    result = response.json()

    assert result["grounded"] is True

    assert len(result["sources"]) == 1

    assert (
        result["workflow_decision"]
        == "continue"
    )

    assert (
        result["escalation_reason"]
        == "normal"
    )

    assert (
        result["requires_human_review"]
        is False
    )

    assert result["review_id"] is None

    reviews = (
        get_pending_rag_reviews_for_student(
            student["id"]
        )
    )

    assert len(reviews) == 0


def test_ungrounded_rag_answer_creates_teacher_review(
    client,
    monkeypatch,
):
    student, _, token = (
        create_student_with_token(
            client
        )
    )

    fallback_answer = (
        "I do not have enough information "
        "in the learning materials to "
        "answer that question."
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": fallback_answer,
            "grounded": False,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Explain quantum teleportation."
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    result = response.json()

    assert result["grounded"] is False

    assert result["sources"] == []

    assert result["answer"] == fallback_answer

    assert (
        result["workflow_decision"]
        == "review"
    )

    assert (
        result["escalation_reason"]
        == "insufficient_evidence"
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert result["review_id"] is not None

    reviews = (
        get_pending_rag_reviews_for_student(
            student["id"]
        )
    )

    matching_reviews = [
        review
        for review in reviews
        if str(review.id)
        == result["review_id"]
    ]

    assert len(matching_reviews) == 1

    review = matching_reviews[0]

    assert (
        review.reason_for_escalation
        == "insufficient_evidence"
    )

    assert review.ai_confidence is None

    assert (
        review.ai_response
        == fallback_answer
    )

    assert (
        review.question_or_activity
        == "Explain quantum teleportation."
    )


def test_same_unsupported_question_reuses_pending_review(
    client,
    monkeypatch,
):
    student, _, token = (
        create_student_with_token(
            client
        )
    )

    fallback_answer = (
        "I do not have enough information "
        "in the learning materials to "
        "answer that question."
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": fallback_answer,
            "grounded": False,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    first_response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Explain dark matter."
            ),
        },
    )

    second_response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "  EXPLAIN   DARK   MATTER.  "
            ),
        },
    )

    assert first_response.status_code == 200

    assert second_response.status_code == 200

    first = first_response.json()
    second = second_response.json()

    assert (
        first["workflow_decision"]
        == "review"
    )

    assert (
        second["workflow_decision"]
        == "review"
    )

    assert (
        first["review_id"]
        == second["review_id"]
    )

    reviews = (
        get_pending_rag_reviews_for_student(
            student["id"]
        )
    )

    matching_reviews = [
        review
        for review in reviews
        if str(review.id)
        == first["review_id"]
    ]

    assert len(matching_reviews) == 1


def test_different_unsupported_questions_create_separate_reviews(
    client,
    monkeypatch,
):
    student, _, token = (
        create_student_with_token(
            client
        )
    )

    fallback_answer = (
        "I do not have enough information "
        "in the learning materials to "
        "answer that question."
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": fallback_answer,
            "grounded": False,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    first_response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Explain dark matter."
            ),
        },
    )

    second_response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Explain gravitational waves."
            ),
        },
    )

    assert first_response.status_code == 200

    assert second_response.status_code == 200

    first = first_response.json()
    second = second_response.json()

    assert first["review_id"] is not None
    assert second["review_id"] is not None

    assert (
        first["review_id"]
        != second["review_id"]
    )

    reviews = (
        get_pending_rag_reviews_for_student(
            student["id"]
        )
    )

    review_ids = {
        str(review.id)
        for review in reviews
    }

    assert first["review_id"] in review_ids

    assert second["review_id"] in review_ids


def test_same_unsupported_question_isolated_between_students(
    client,
    monkeypatch,
):
    student_a, _, token_a = (
        create_student_with_token(
            client,
            full_name="RAG Student A",
        )
    )

    student_b, _, token_b = (
        create_student_with_token(
            client,
            full_name="RAG Student B",
        )
    )

    fallback_answer = (
        "I do not have enough information "
        "in the learning materials to "
        "answer that question."
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": fallback_answer,
            "grounded": False,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    question = (
        "Explain superconductivity."
    )

    response_a = client.post(
        "/rag/ask",
        headers=auth_headers(token_a),
        json={
            "question": question,
        },
    )

    response_b = client.post(
        "/rag/ask",
        headers=auth_headers(token_b),
        json={
            "question": question,
        },
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    result_a = response_a.json()
    result_b = response_b.json()

    assert result_a["review_id"] is not None
    assert result_b["review_id"] is not None

    assert (
        result_a["review_id"]
        != result_b["review_id"]
    )

    reviews_a = (
        get_pending_rag_reviews_for_student(
            student_a["id"]
        )
    )

    reviews_b = (
        get_pending_rag_reviews_for_student(
            student_b["id"]
        )
    )

    review_ids_a = {
        str(review.id)
        for review in reviews_a
    }

    review_ids_b = {
        str(review.id)
        for review in reviews_b
    }

    assert (
        result_a["review_id"]
        in review_ids_a
    )

    assert (
        result_a["review_id"]
        not in review_ids_b
    )

    assert (
        result_b["review_id"]
        in review_ids_b
    )

    assert (
        result_b["review_id"]
        not in review_ids_a
    )


def test_grounded_flag_without_sources_is_treated_as_insufficient_evidence(
    client,
    monkeypatch,
):
    _, _, token = (
        create_student_with_token(
            client
        )
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": (
                "This answer claims grounding "
                "but has no source evidence."
            ),
            "grounded": True,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "Test evidence consistency."
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    result = response.json()

    assert result["grounded"] is True

    assert result["sources"] == []

    assert (
        result["workflow_decision"]
        == "review"
    )

    assert (
        result["escalation_reason"]
        == "insufficient_evidence"
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert result["review_id"] is not None


def test_rag_hitl_does_not_invent_numeric_ai_confidence(
    client,
    monkeypatch,
):
    student, _, token = (
        create_student_with_token(
            client
        )
    )

    def fake_answer(question: str):
        return {
            "question": question,
            "answer": (
                "I do not have enough information "
                "in the learning materials to "
                "answer that question."
            ),
            "grounded": False,
            "sources": [],
        }

    monkeypatch.setattr(
        "app.api.routes.rag.rag_service.answer",
        fake_answer,
    )

    response = client.post(
        "/rag/ask",
        headers=auth_headers(token),
        json={
            "question": (
                "What is a warp drive?"
            ),
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["review_id"] is not None

    reviews = (
        get_pending_rag_reviews_for_student(
            student["id"]
        )
    )

    matching_review = next(
        review
        for review in reviews
        if str(review.id)
        == result["review_id"]
    )

    assert matching_review.ai_confidence is None