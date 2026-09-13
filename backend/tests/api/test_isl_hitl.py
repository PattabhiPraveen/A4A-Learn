import uuid
from unittest.mock import patch

from app.database.database import SessionLocal
from app.models.learning_review import LearningReview
from app.models.user import User


TEST_PASSWORD = "A4A_Test_2026!"


def create_user_and_token(
    client,
    *,
    name: str = "ISL HITL Student",
):
    """
    Create an isolated learner and return:
    (user_id, access_token)
    """

    email = (
        f"isl_hitl_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": name,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert registration.status_code == 201, (
        registration.text
    )

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .one()
        )

        user_id = user.id

    finally:
        db.close()

    return user_id, token


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def fake_image_file():
    """
    The route validates extension/content type before
    landmark extraction. The mocked extractor means
    the bytes do not need to contain a real image.
    """

    return {
        "file": (
            "test.jpeg",
            b"fake-image-content",
            "image/jpeg",
        )
    }


def get_student_reviews(
    student_id,
):
    db = SessionLocal()

    try:
        return (
            db.query(LearningReview)
            .filter(
                LearningReview.student_id
                == student_id
            )
            .order_by(
                LearningReview.created_at.asc()
            )
            .all()
        )

    finally:
        db.close()


def post_prediction(
    client,
    *,
    token: str,
    target_letter: str,
):
    return client.post(
        "/isl/predict",
        headers=auth_headers(token),
        data={
            "target_letter": target_letter,
        },
        files=fake_image_file(),
    )


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_high_confidence_correct_attempt_continues(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": "A",
        "predicted_label": "A",
        "confidence": 0.95,
        "accepted": True,
        "threshold": 0.70,
        "model": "test-model",
    }

    response = post_prediction(
        client,
        token=token,
        target_letter="A",
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["is_correct"] is True
    assert data["workflow_decision"] == (
        "continue"
    )
    assert data["escalation_reason"] == (
        "normal"
    )
    assert (
        data["requires_human_review"]
        is False
    )
    assert data["review_id"] is None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 0


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_first_low_confidence_attempt_retries(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    response = post_prediction(
        client,
        token=token,
        target_letter="D",
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["workflow_decision"] == (
        "retry"
    )
    assert data["escalation_reason"] == (
        "low_confidence"
    )
    assert (
        data["requires_human_review"]
        is False
    )
    assert data["review_id"] is None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 0


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_second_low_confidence_attempt_still_retries(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    first = post_prediction(
        client,
        token=token,
        target_letter="D",
    )

    second = post_prediction(
        client,
        token=token,
        target_letter="D",
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_data = first.json()
    second_data = second.json()

    assert first_data[
        "workflow_decision"
    ] == "retry"

    assert second_data[
        "workflow_decision"
    ] == "retry"

    assert second_data[
        "requires_human_review"
    ] is False

    assert second_data["review_id"] is None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 0


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_third_weak_attempt_creates_review(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    responses = [
        post_prediction(
            client,
            token=token,
            target_letter="D",
        )
        for _ in range(3)
    ]

    assert all(
        response.status_code == 200
        for response in responses
    )

    assert responses[0].json()[
        "workflow_decision"
    ] == "retry"

    assert responses[1].json()[
        "workflow_decision"
    ] == "retry"

    third = responses[2].json()

    assert third[
        "workflow_decision"
    ] == "review"

    assert third[
        "escalation_reason"
    ] == "repeated_difficulty"

    assert third[
        "requires_human_review"
    ] is True

    assert third["review_id"] is not None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 1

    review = reviews[0]

    assert review.status == "pending"
    assert review.activity_type == "isl"
    assert (
        review.activity_reference_id
        == "isl:D"
    )
    assert (
        review.reason_for_escalation
        == "repeated_difficulty"
    )
    assert review.student_attempts == 3


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_fourth_weak_attempt_reuses_pending_review(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    responses = [
        post_prediction(
            client,
            token=token,
            target_letter="D",
        )
        for _ in range(4)
    ]

    third = responses[2].json()
    fourth = responses[3].json()

    assert third[
        "workflow_decision"
    ] == "review"

    assert fourth[
        "workflow_decision"
    ] == "review"

    assert third["review_id"] is not None

    assert (
        fourth["review_id"]
        == third["review_id"]
    )

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 1


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
def test_first_no_hand_attempt_retries(
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = None

    response = post_prediction(
        client,
        token=token,
        target_letter="E",
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["hand_detected"] is False
    assert data["confidence"] == 0.0

    assert data[
        "workflow_decision"
    ] == "retry"

    assert data[
        "escalation_reason"
    ] == "low_confidence"

    assert (
        data["requires_human_review"]
        is False
    )

    assert data["review_id"] is None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 0


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
def test_repeated_no_hand_attempts_create_review(
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = None

    responses = [
        post_prediction(
            client,
            token=token,
            target_letter="E",
        )
        for _ in range(3)
    ]

    assert responses[0].json()[
        "workflow_decision"
    ] == "retry"

    assert responses[1].json()[
        "workflow_decision"
    ] == "retry"

    third = responses[2].json()

    assert third[
        "workflow_decision"
    ] == "review"

    assert third[
        "escalation_reason"
    ] == "repeated_difficulty"

    assert third[
        "requires_human_review"
    ] is True

    assert third["review_id"] is not None

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 1

    assert (
        reviews[0].activity_reference_id
        == "isl:E"
    )


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_reviews_are_isolated_by_student(
    mock_predict,
    mock_extractor_class,
    client,
):
    student_1_id, token_1 = (
        create_user_and_token(
            client,
            name="Student One",
        )
    )

    student_2_id, token_2 = (
        create_user_and_token(
            client,
            name="Student Two",
        )
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    for _ in range(3):
        response = post_prediction(
            client,
            token=token_1,
            target_letter="D",
        )

        assert response.status_code == 200

    for _ in range(3):
        response = post_prediction(
            client,
            token=token_2,
            target_letter="D",
        )

        assert response.status_code == 200

    reviews_1 = get_student_reviews(
        student_1_id
    )

    reviews_2 = get_student_reviews(
        student_2_id
    )

    assert len(reviews_1) == 1
    assert len(reviews_2) == 1

    assert (
        reviews_1[0].id
        != reviews_2[0].id
    )

    assert (
        reviews_1[0].student_id
        == student_1_id
    )

    assert (
        reviews_2[0].student_id
        == student_2_id
    )


@patch(
    "app.api.routes.isl.HandLandmarkExtractor"
)
@patch(
    "app.api.routes.isl.predictor.predict"
)
def test_reviews_are_isolated_by_target_letter(
    mock_predict,
    mock_extractor_class,
    client,
):
    user_id, token = create_user_and_token(
        client
    )

    extractor = (
        mock_extractor_class.return_value
    )

    extractor.extract.return_value = [
        0.0
    ] * 63

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "D",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    for _ in range(3):
        response = post_prediction(
            client,
            token=token,
            target_letter="D",
        )

        assert response.status_code == 200

    mock_predict.return_value = {
        "label": None,
        "predicted_label": "E",
        "confidence": 0.40,
        "accepted": False,
        "threshold": 0.70,
        "model": "test-model",
    }

    for _ in range(3):
        response = post_prediction(
            client,
            token=token,
            target_letter="E",
        )

        assert response.status_code == 200

    reviews = get_student_reviews(
        user_id
    )

    assert len(reviews) == 2

    references = {
        review.activity_reference_id
        for review in reviews
    }

    assert references == {
        "isl:D",
        "isl:E",
    }
