import uuid


def create_test_user(client):

    email = f"security_{uuid.uuid4().hex[:8]}@a4alearn.com"

    payload = {
        "full_name": "Security Test Student",
        "email": email,
        "password": "A4A_Test_2026!",
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    return email


def test_profile_requires_authentication(client):

    response = client.get("/users/me")

    assert response.status_code == 401


def test_wrong_password_rejected(client):

    email = create_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_invalid_token_rejected(client):

    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401