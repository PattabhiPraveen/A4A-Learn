import uuid

from app.services.learning_content_service import (
    LearningContentService,
)


TEST_PASSWORD = "A4A_Test_2026!"


def create_user_and_token(client):
    """
    Create an isolated learner and return an access token.
    """
    email = (
        f"learning_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Learning Test Student",
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert registration.status_code == 201, registration.text

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200, login.text

    return login.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def test_learning_lessons_requires_authentication(client):
    response = client.get(
        "/learning/lessons"
    )

    assert response.status_code == 401


def test_learning_lesson_detail_requires_authentication(client):
    response = client.get(
        "/learning/lessons/lesson_01"
    )

    assert response.status_code == 401


def test_list_governed_learning_lessons(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    lessons = response.json()

    assert len(lessons) == 6

    assert [lesson["id"] for lesson in lessons] == [
        "lesson_01",
        "lesson_02",
        "lesson_03",
        "lesson_04",
        "lesson_05",
        "lesson_06",
    ]

    assert [
        lesson["curriculum_id"]
        for lesson in lessons
    ] == [
        "PY-01",
        "PY-02",
        "PY-03",
        "AI-01",
        "AI-02",
        "AI-03",
    ]

    assert [
        lesson["title"]
        for lesson in lessons
    ] == [
        "Introduction to Python",
        "Variables and Data Types",
        "Conditions and Loops",
        "Introduction to Artificial Intelligence",
        "Machine Learning Basics",
        "Generative AI and Responsible AI",
    ]

    assert [
        lesson["course"]
        for lesson in lessons
    ] == [
        "Python",
        "Python",
        "Python",
        "Artificial Intelligence",
        "Artificial Intelligence",
        "Artificial Intelligence",
    ]

    assert [
        lesson["sequence"]
        for lesson in lessons
    ] == [
        1,
        2,
        3,
        1,
        2,
        3,
    ]

    assert [
        lesson["estimated_minutes"]
        for lesson in lessons
    ] == [
        15,
        20,
        25,
        15,
        20,
        25,
    ]

    for lesson in lessons:
        assert lesson["level"] == "Beginner"
        assert lesson["description"]
        assert lesson["topic"]
        assert lesson["course"]

        # List endpoint intentionally returns summaries.
        assert "content" not in lesson


def test_get_python_lesson_detail(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons/lesson_01",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    lesson = response.json()

    assert lesson["id"] == "lesson_01"
    assert lesson["curriculum_id"] == "PY-01"
    assert lesson["title"] == "Introduction to Python"
    assert lesson["course"] == "Python"
    assert lesson["topic"] == "Python"
    assert lesson["level"] == "Beginner"
    assert lesson["sequence"] == 1
    assert lesson["estimated_minutes"] == 15

    assert (
        "what Python is"
        in lesson["content"]
    )

    assert (
        'print("Hello, A4A Learn!")'
        in lesson["content"]
    )

    # Front matter and H1 title must not leak into content.
    assert "id: PY-01" not in lesson["content"]
    assert "# Introduction to Python" not in lesson["content"]


def test_get_ai_lesson_detail(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons/lesson_06",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    lesson = response.json()

    assert lesson["id"] == "lesson_06"
    assert lesson["curriculum_id"] == "AI-03"

    assert lesson["title"] == (
        "Generative AI and Responsible AI"
    )

    assert lesson["course"] == (
        "Artificial Intelligence"
    )

    assert lesson["topic"] == (
        "Artificial Intelligence"
    )

    assert lesson["level"] == "Beginner"
    assert lesson["sequence"] == 3
    assert lesson["estimated_minutes"] == 25

    assert (
        "Retrieval-Augmented Generation"
        in lesson["content"]
    )

    assert (
        "Responsible AI"
        in lesson["content"]
    )


def test_unknown_learning_lesson_returns_404(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons/lesson_99",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Learning lesson not found."
    )


def test_invalid_learning_lesson_id_returns_404(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons/DOC001",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_path_traversal_is_not_exposed(client):
    token = create_user_and_token(client)

    response = client.get(
        "/learning/lessons/%2E%2E%2FREADME",
        headers=auth_headers(token),
    )

    assert response.status_code in {
        404,
        422,
    }


def test_learning_service_excludes_benchmark_corpus():
    service = LearningContentService()

    lessons = service.list_lessons()

    lesson_ids = {
        lesson.id
        for lesson in lessons
    }

    assert lesson_ids == {
        "lesson_01",
        "lesson_02",
        "lesson_03",
        "lesson_04",
        "lesson_05",
        "lesson_06",
    }

    assert not any(
        lesson_id.startswith("DOC")
        for lesson_id in lesson_ids
    )


def test_governed_curriculum_contract():
    service = LearningContentService()

    lessons = service.list_lessons()

    curriculum_ids = {
        lesson.curriculum_id
        for lesson in lessons
    }

    assert curriculum_ids == {
        "PY-01",
        "PY-02",
        "PY-03",
        "AI-01",
        "AI-02",
        "AI-03",
    }

    python_lessons = [
        lesson
        for lesson in lessons
        if lesson.course == "Python"
    ]

    ai_lessons = [
        lesson
        for lesson in lessons
        if lesson.course == "Artificial Intelligence"
    ]

    assert [
        lesson.sequence
        for lesson in python_lessons
    ] == [1, 2, 3]

    assert [
        lesson.sequence
        for lesson in ai_lessons
    ] == [1, 2, 3]