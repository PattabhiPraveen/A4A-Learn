import uuid

from fastapi.testclient import TestClient


TEST_PASSWORD = "A4A_Test_2026!"


def create_user_and_token(
    client: TestClient,
    *,
    prefix: str = "progress",
) -> tuple[str, str]:
    """
    Create a unique student and return:
    (email, access_token)
    """

    unique = uuid.uuid4().hex[:10]
    email = f"{prefix}_{unique}@example.com"

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Progress Test Student",
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

    body = login.json()

    assert "access_token" in body

    return email, body["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_progress_me_requires_authentication(client):
    response = client.get("/progress/me")

    assert response.status_code == 401


def test_create_isl_attempt_requires_authentication(client):
    response = client.post(
        "/progress/isl-attempts",
        json={
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 0.90,
            "accepted": True,
        },
    )

    assert response.status_code == 401


def test_record_correct_isl_attempt(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 0.90,
            "accepted": True,
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["target_letter"] == "A"
    assert body["predicted_letter"] == "A"
    assert body["accepted"] is True
    assert body["is_correct"] is True
    assert body["confidence"] == 0.90
    assert "id" in body
    assert "created_at" in body


def test_matching_prediction_not_accepted_is_not_correct(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "B",
            "predicted_letter": "B",
            "confidence": 0.55,
            "accepted": False,
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["target_letter"] == "B"
    assert body["predicted_letter"] == "B"
    assert body["accepted"] is False
    assert body["is_correct"] is False


def test_wrong_prediction_is_not_correct(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "C",
            "predicted_letter": "D",
            "confidence": 0.91,
            "accepted": True,
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["accepted"] is True
    assert body["is_correct"] is False


def test_progress_normalizes_letters(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "a",
            "predicted_letter": "A",
            "confidence": 0.88,
            "accepted": True,
        },
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["target_letter"] == "A"
    assert body["predicted_letter"] == "A"
    assert body["is_correct"] is True


def test_invalid_target_letter_rejected(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "1",
            "predicted_letter": "A",
            "confidence": 0.90,
            "accepted": True,
        },
    )

    assert response.status_code == 422


def test_invalid_confidence_rejected(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 1.50,
            "accepted": True,
        },
    )

    assert response.status_code == 422


def test_client_cannot_submit_is_correct(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": "A",
            "predicted_letter": "B",
            "confidence": 0.95,
            "accepted": True,
            "is_correct": True,
        },
    )

    assert response.status_code == 422


def test_client_cannot_submit_user_id(client):
    _, token = create_user_and_token(client)

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "user_id": str(uuid.uuid4()),
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 0.95,
            "accepted": True,
        },
    )

    assert response.status_code == 422


def test_progress_summary_for_authenticated_user(client):
    _, token = create_user_and_token(client)

    headers = auth_headers(token)

    attempts = [
        {
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 0.90,
            "accepted": True,
        },
        {
            "target_letter": "B",
            "predicted_letter": "B",
            "confidence": 0.50,
            "accepted": False,
        },
        {
            "target_letter": "C",
            "predicted_letter": "D",
            "confidence": 0.91,
            "accepted": True,
        },
    ]

    for payload in attempts:
        response = client.post(
            "/progress/isl-attempts",
            headers=headers,
            json=payload,
        )

        assert response.status_code == 201, response.text

    response = client.get(
        "/progress/me",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["total_attempts"] == 3
    assert body["correct_attempts"] == 1
    assert body["incorrect_attempts"] == 2
    assert body["accuracy_percent"] == 33.33


def test_progress_is_isolated_between_users(client):
    _, token_a = create_user_and_token(
        client,
        prefix="student_a",
    )

    _, token_b = create_user_and_token(
        client,
        prefix="student_b",
    )

    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token_a),
        json={
            "target_letter": "A",
            "predicted_letter": "A",
            "confidence": 0.94,
            "accepted": True,
        },
    )

    assert response.status_code == 201, response.text

    response_a = client.get(
        "/progress/me",
        headers=auth_headers(token_a),
    )

    response_b = client.get(
        "/progress/me",
        headers=auth_headers(token_b),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    progress_a = response_a.json()
    progress_b = response_b.json()

    assert progress_a["total_attempts"] == 1
    assert progress_a["correct_attempts"] == 1

    assert progress_b["total_attempts"] == 0
    assert progress_b["correct_attempts"] == 0
    assert progress_b["accuracy_percent"] == 0.0

    assert progress_a["user_id"] != progress_b["user_id"]