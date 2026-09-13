from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2].parent

TEST_IMAGE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "DS002_ISL_Alphabet"
    / "A"
    / "1.jpeg"
)


def create_user_and_token(client):

    import uuid

    email = (
        f"isl_{uuid.uuid4().hex[:8]}"
        "@a4alearn.com"
    )

    password = "A4A_Test_2026!"

    registration = client.post(
        "/auth/register",
        json={
            "full_name": "ISL Test Student",
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


def test_isl_requires_authentication(client):

    with TEST_IMAGE.open("rb") as image:

        response = client.post(
            "/isl/predict",
            data={
                "target_letter": "A",
            },
            files={
                "file": (
                    "1.jpeg",
                    image,
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 401


def test_isl_predict_known_image(client):

    token = create_user_and_token(client)

    with TEST_IMAGE.open("rb") as image:

        response = client.post(
            "/isl/predict",
            headers={
                "Authorization": (
                    f"Bearer {token}"
                )
            },
            data={
                "target_letter": "A",
            },
            files={
                "file": (
                    "1.jpeg",
                    image,
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 200, response.text

    data = response.json()

    # Existing ISL inference validation
    assert data["hand_detected"] is True
    assert data["predicted_label"] == "A"
    assert data["accepted"] is True
    assert data["label"] == "A"

    assert 0.0 <= data["confidence"] <= 1.0

    # Sprint 4 Step 4.9:
    # authoritative prediction persistence validation
    assert data["target_letter"] == "A"
    assert data["is_correct"] is True
    assert data["attempt_id"] is not None


def test_isl_rejects_unsupported_file(client):

    token = create_user_and_token(client)

    response = client.post(
        "/isl/predict",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
        data={
            "target_letter": "A",
        },
        files={
            "file": (
                "test.txt",
                b"not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415