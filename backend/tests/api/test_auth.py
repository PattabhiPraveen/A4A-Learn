import uuid


def test_user_registration_login_and_profile(client):

    email = f"test_{uuid.uuid4().hex[:8]}@a4alearn.com"

    registration_payload = {
        "full_name": "Automated Test Student",
        "email": email,
        "password": "A4A_Test_2026!",
    }

    # ---------------------------------
    # Registration
    # ---------------------------------

    response = client.post(
        "/auth/register",
        json=registration_payload,
    )

    assert response.status_code == 201

    user = response.json()

    assert user["full_name"] == "Automated Test Student"
    assert user["email"] == email
    assert user["role"] == "student"
    assert user["is_active"] is True

    user_id = user["id"]

    # ---------------------------------
    # Login
    # ---------------------------------

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "A4A_Test_2026!",
        },
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]

    # ---------------------------------
    # Protected endpoint
    # ---------------------------------

    profile_response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["id"] == user_id
    assert profile["email"] == email
    assert profile["role"] == "student"