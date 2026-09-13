import uuid


def create_user_and_token(
    client,
    *,
    prefix: str = "analytics",
):
    email = (
        f"{prefix}_"
        f"{uuid.uuid4().hex[:8]}"
        "@a4alearn.com"
    )

    password = "A4A_Test_2026!"

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Analytics Test Student",
            "email": email,
            "password": password,
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def record_attempt(
    client,
    token,
    *,
    target_letter,
    predicted_letter,
    confidence,
    accepted,
):
    response = client.post(
        "/progress/isl-attempts",
        headers=auth_headers(token),
        json={
            "target_letter": target_letter,
            "predicted_letter": predicted_letter,
            "confidence": confidence,
            "accepted": accepted,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_analytics_requires_authentication(
    client,
):
    response = client.get(
        "/progress/me/analytics"
    )

    assert response.status_code == 401


def test_empty_learner_analytics(
    client,
):
    token = create_user_and_token(
        client,
        prefix="empty",
    )

    response = client.get(
        "/progress/me/analytics",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["overall"]["total_attempts"] == 0
    assert data["overall"]["correct_attempts"] == 0
    assert data["overall"]["incorrect_attempts"] == 0
    assert data["overall"]["accuracy_percent"] == 0.0

    assert data["letters_attempted"] == 0
    assert data["letter_performance"] == []

    assert data["weak_letters"] == []
    assert data["weak_letter_count"] == 0

    assert data["low_confidence_attempts"] == 0
    assert data["recent_attempts"] == []


def test_per_letter_analytics(
    client,
):
    token = create_user_and_token(
        client,
        prefix="letter",
    )

    record_attempt(
        client,
        token,
        target_letter="A",
        predicted_letter="A",
        confidence=0.95,
        accepted=True,
    )

    record_attempt(
        client,
        token,
        target_letter="A",
        predicted_letter="B",
        confidence=0.85,
        accepted=True,
    )

    record_attempt(
        client,
        token,
        target_letter="A",
        predicted_letter="A",
        confidence=0.50,
        accepted=False,
    )

    response = client.get(
        "/progress/me/analytics",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["overall"]["total_attempts"] == 3
    assert data["overall"]["correct_attempts"] == 1
    assert data["overall"]["incorrect_attempts"] == 2
    assert data["overall"]["accuracy_percent"] == 33.33

    assert data["letters_attempted"] == 1

    assert len(
        data["letter_performance"]
    ) == 1

    letter = data[
        "letter_performance"
    ][0]

    assert letter["target_letter"] == "A"
    assert letter["total_attempts"] == 3
    assert letter["correct_attempts"] == 1
    assert letter["incorrect_attempts"] == 2
    assert letter["accepted_attempts"] == 2

    assert letter["accuracy_percent"] == 33.33

    assert (
        letter["acceptance_rate_percent"]
        == 66.67
    )

    assert letter["weak_candidate"] is True

    assert data["weak_letter_count"] == 1

    assert (
        data["weak_letters"][0][
            "target_letter"
        ]
        == "A"
    )

    assert data["low_confidence_attempts"] == 1


def test_single_failure_not_weak_candidate(
    client,
):
    token = create_user_and_token(
        client,
        prefix="single",
    )

    record_attempt(
        client,
        token,
        target_letter="B",
        predicted_letter="C",
        confidence=0.80,
        accepted=True,
    )

    response = client.get(
        "/progress/me/analytics",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    letter = data[
        "letter_performance"
    ][0]

    assert letter["target_letter"] == "B"
    assert letter["total_attempts"] == 1
    assert letter["accuracy_percent"] == 0.0

    assert letter["weak_candidate"] is False
    assert data["weak_letter_count"] == 0


def test_exact_60_percent_not_weak(
    client,
):
    token = create_user_and_token(
        client,
        prefix="boundary",
    )

    outcomes = [
        ("C", "C", 0.90, True),
        ("C", "C", 0.90, True),
        ("C", "C", 0.90, True),
        ("C", "D", 0.90, True),
        ("C", "D", 0.90, True),
    ]

    for (
        target,
        predicted,
        confidence,
        accepted,
    ) in outcomes:
        record_attempt(
            client,
            token,
            target_letter=target,
            predicted_letter=predicted,
            confidence=confidence,
            accepted=accepted,
        )

    response = client.get(
        "/progress/me/analytics",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    letter = data[
        "letter_performance"
    ][0]

    assert letter["total_attempts"] == 5
    assert letter["correct_attempts"] == 3
    assert letter["accuracy_percent"] == 60.0

    assert letter["weak_candidate"] is False


def test_recent_limit(
    client,
):
    token = create_user_and_token(
        client,
        prefix="recent",
    )

    for _ in range(5):
        record_attempt(
            client,
            token,
            target_letter="D",
            predicted_letter="D",
            confidence=0.90,
            accepted=True,
        )

    response = client.get(
        "/progress/me/analytics?recent_limit=2",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data["recent_attempts"]
    ) == 2


def test_invalid_recent_limit_rejected(
    client,
):
    token = create_user_and_token(
        client,
        prefix="limit",
    )

    response = client.get(
        "/progress/me/analytics?recent_limit=0",
        headers=auth_headers(token),
    )

    assert response.status_code == 422

    response = client.get(
        "/progress/me/analytics?recent_limit=51",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_analytics_cross_user_isolation(
    client,
):
    token_a = create_user_and_token(
        client,
        prefix="usera",
    )

    token_b = create_user_and_token(
        client,
        prefix="userb",
    )

    record_attempt(
        client,
        token_a,
        target_letter="A",
        predicted_letter="A",
        confidence=0.95,
        accepted=True,
    )

    record_attempt(
        client,
        token_a,
        target_letter="B",
        predicted_letter="B",
        confidence=0.95,
        accepted=True,
    )

    response_b = client.get(
        "/progress/me/analytics",
        headers=auth_headers(token_b),
    )

    assert response_b.status_code == 200

    data_b = response_b.json()

    assert data_b["overall"]["total_attempts"] == 0
    assert data_b["letters_attempted"] == 0
    assert data_b["letter_performance"] == []
    assert data_b["recent_attempts"] == []
