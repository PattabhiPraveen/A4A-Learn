import uuid

import pytest


TEST_PASSWORD = "A4A_Test_2026!"


def create_authenticated_student(client):
    """
    Register a unique student, log in, and return
    the bearer token plus the registered user.
    """

    email = f"accessibility_{uuid.uuid4().hex[:8]}@a4alearn.com"

    registration_payload = {
        "full_name": "Accessibility Test Student",
        "email": email,
        "password": TEST_PASSWORD,
    }

    registration_response = client.post(
        "/auth/register",
        json=registration_payload,
    )

    assert registration_response.status_code == 201

    registered_user = registration_response.json()

    assert registered_user["email"] == email
    assert registered_user["role"] == "student"
    assert registered_user["is_active"] is True

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    return (
        token_data["access_token"],
        registered_user,
    )


def authorization_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_default_accessibility_profile_on_registration(client):
    """
    A newly registered learner should receive
    safe accessibility defaults.
    """

    token, registered_user = create_authenticated_student(client)

    assert registered_user["accessibility_profile"] == "standard"
    assert registered_user["preferred_language"] == "english"
    assert registered_user["isl_enabled"] is False
    assert registered_user["captions_enabled"] is False

    profile_response = client.get(
        "/users/me",
        headers=authorization_headers(token),
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["accessibility_profile"] == "standard"
    assert profile["preferred_language"] == "english"
    assert profile["isl_enabled"] is False
    assert profile["captions_enabled"] is False


def test_accessibility_update_requires_authentication(client):
    """
    The accessibility endpoint must reject
    unauthenticated updates.
    """

    response = client.patch(
        "/users/me/accessibility",
        json={
            "accessibility_profile": "deaf",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": True,
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    (
        "accessibility_profile",
        "isl_enabled",
        "captions_enabled",
    ),
    [
        ("standard", False, False),
        ("deaf", True, True),
        ("hard_of_hearing", False, True),
        ("non_speaking", True, False),
    ],
)
def test_supported_accessibility_profiles(
    client,
    accessibility_profile,
    isl_enabled,
    captions_enabled,
):
    """
    Every supported accessibility profile should
    be accepted and returned by the API.
    """

    token, _ = create_authenticated_student(client)

    response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": accessibility_profile,
            "preferred_language": "english",
            "isl_enabled": isl_enabled,
            "captions_enabled": captions_enabled,
        },
    )

    assert response.status_code == 200

    updated_user = response.json()

    assert (
        updated_user["accessibility_profile"]
        == accessibility_profile
    )
    assert updated_user["preferred_language"] == "english"
    assert updated_user["isl_enabled"] is isl_enabled
    assert updated_user["captions_enabled"] is captions_enabled


def test_accessibility_preferences_persist_in_user_profile(client):
    """
    Preferences saved through PATCH must remain
    available through GET /users/me.
    """

    token, registered_user = create_authenticated_student(client)

    update_response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "deaf",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": True,
        },
    )

    assert update_response.status_code == 200

    profile_response = client.get(
        "/users/me",
        headers=authorization_headers(token),
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["id"] == registered_user["id"]
    assert profile["email"] == registered_user["email"]
    assert profile["accessibility_profile"] == "deaf"
    assert profile["preferred_language"] == "english"
    assert profile["isl_enabled"] is True
    assert profile["captions_enabled"] is True


def test_accessibility_preferences_can_be_changed_again(client):
    """
    A learner must be able to change previously
    saved accessibility preferences.
    """

    token, _ = create_authenticated_student(client)

    first_response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "deaf",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": True,
        },
    )

    assert first_response.status_code == 200

    second_response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "hard_of_hearing",
            "preferred_language": "english",
            "isl_enabled": False,
            "captions_enabled": True,
        },
    )

    assert second_response.status_code == 200

    updated_user = second_response.json()

    assert (
        updated_user["accessibility_profile"]
        == "hard_of_hearing"
    )
    assert updated_user["isl_enabled"] is False
    assert updated_user["captions_enabled"] is True

    profile_response = client.get(
        "/users/me",
        headers=authorization_headers(token),
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert (
        profile["accessibility_profile"]
        == "hard_of_hearing"
    )
    assert profile["isl_enabled"] is False
    assert profile["captions_enabled"] is True


def test_invalid_accessibility_profile_is_rejected(client):
    """
    Unsupported accessibility profile values
    must fail schema validation.
    """

    token, _ = create_authenticated_student(client)

    response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "invalid_profile",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": True,
        },
    )

    assert response.status_code == 422


def test_accessibility_update_does_not_change_role(client):
    """
    Accessibility personalization must never
    change authorization role.
    """

    token, registered_user = create_authenticated_student(client)

    assert registered_user["role"] == "student"

    update_response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "deaf",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": True,
        },
    )

    assert update_response.status_code == 200

    updated_user = update_response.json()

    assert updated_user["role"] == "student"

    profile_response = client.get(
        "/users/me",
        headers=authorization_headers(token),
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["role"] == "student"


def test_existing_token_remains_valid_after_accessibility_update(client):
    """
    Changing accessibility preferences must not
    require a new JWT or a new login.
    """

    token, registered_user = create_authenticated_student(client)

    update_response = client.patch(
        "/users/me/accessibility",
        headers=authorization_headers(token),
        json={
            "accessibility_profile": "non_speaking",
            "preferred_language": "english",
            "isl_enabled": True,
            "captions_enabled": False,
        },
    )

    assert update_response.status_code == 200

    profile_response = client.get(
        "/users/me",
        headers=authorization_headers(token),
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["id"] == registered_user["id"]
    assert profile["role"] == "student"
    assert profile["accessibility_profile"] == "non_speaking"
    assert profile["isl_enabled"] is True
    assert profile["captions_enabled"] is False