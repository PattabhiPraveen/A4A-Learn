import uuid

from app.database.database import SessionLocal
from app.models.user import User


TEST_PASSWORD = "A4A_Test_2026!"


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_student_with_token(
    client,
    *,
    full_name: str = "Review Test Student",
):
    """
    Create an isolated student and return:

    (
        user_id,
        email,
        access_token,
    )
    """

    email = (
        f"review_student_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": full_name,
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

    return user_id, email, token


def create_teacher_with_token(
    client,
    *,
    full_name: str = "Review Test Teacher",
):
    """
    Create a normal user, promote the user to teacher
    in the database, and then authenticate.

    Teacher authorization is therefore validated against
    the actual persisted user role.
    """

    email = (
        f"review_teacher_{uuid.uuid4().hex[:10]}"
        "@a4alearn.com"
    )

    registration = client.post(
        "/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert registration.status_code == 201, (
        registration.text
    )

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .one()
        )

        user.role = "teacher"

        db.commit()
        db.refresh(user)

        user_id = user.id

    finally:
        db.close()

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    return user_id, email, token


def create_review(
    client,
    *,
    token: str,
    activity_reference_id: str | None = None,
    question: str = (
        "I need help understanding this activity."
    ),
):
    """
    Create a learner-requested human review.
    """

    payload = {
        "activity_type": "isl",
        "question_or_activity": question,
    }

    if activity_reference_id is not None:
        payload[
            "activity_reference_id"
        ] = activity_reference_id

    response = client.post(
        "/reviews/request",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    return response.json()


def get_pending_review_from_paginated_queue(
    client,
    *,
    teacher_token: str,
    review_id: str,
):
    """
    Search the teacher pending-review queue using the
    production pagination contract.

    This intentionally does not assume the requested
    review is present on the first page.

    It makes this test deterministic even when the local
    development/test database contains many historical
    pending review records.
    """

    limit = 100
    offset = 0

    while True:
        response = client.get(
            "/reviews/pending",
            headers=auth_headers(
                teacher_token
            ),
            params={
                "limit": limit,
                "offset": offset,
            },
        )

        assert response.status_code == 200, (
            response.text
        )

        reviews = response.json()

        for review in reviews:
            if review["id"] == review_id:
                return review

        if len(reviews) < limit:
            return None

        offset += limit


def test_review_endpoints_require_authentication(
    client,
):
    me_response = client.get(
        "/reviews/me",
    )

    assert me_response.status_code == 401

    pending_response = client.get(
        "/reviews/pending",
    )

    assert pending_response.status_code == 401


def test_student_can_request_teacher_review(
    client,
):
    student_id, _, token = (
        create_student_with_token(
            client
        )
    )

    result = create_review(
        client,
        token=token,
        activity_reference_id=(
            f"isl-{uuid.uuid4().hex}"
        ),
        question=(
            "I keep having difficulty signing "
            "the letter D."
        ),
    )

    assert result["decision"] == "review"

    assert (
        result["reason"]
        == "student_requested_help"
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert result["review_created"] is True

    review = result["review"]

    assert review is not None

    assert (
        review["student_id"]
        == str(student_id)
    )

    assert review["activity_type"] == "isl"

    assert review["status"] == "pending"

    assert (
        review["reason_for_escalation"]
        == "student_requested_help"
    )

    assert review["teacher_feedback"] is None

    assert review["reviewed_by"] is None

    assert review["reviewed_at"] is None


def test_student_cannot_supply_student_id(
    client,
):
    _, _, token = create_student_with_token(
        client
    )

    response = client.post(
        "/reviews/request",
        headers=auth_headers(token),
        json={
            "student_id": str(
                uuid.uuid4()
            ),
            "activity_type": "isl",
            "question_or_activity": (
                "Please help me."
            ),
        },
    )

    assert response.status_code == 422


def test_student_can_view_only_own_reviews(
    client,
):
    student_a_id, _, token_a = (
        create_student_with_token(
            client,
            full_name="Student A",
        )
    )

    student_b_id, _, token_b = (
        create_student_with_token(
            client,
            full_name="Student B",
        )
    )

    review_a = create_review(
        client,
        token=token_a,
        activity_reference_id=(
            f"A-{uuid.uuid4().hex}"
        ),
        question="Student A review request",
    )

    review_b = create_review(
        client,
        token=token_b,
        activity_reference_id=(
            f"B-{uuid.uuid4().hex}"
        ),
        question="Student B review request",
    )

    response_a = client.get(
        "/reviews/me",
        headers=auth_headers(token_a),
    )

    assert response_a.status_code == 200

    student_a_reviews = (
        response_a.json()
    )

    student_a_review_ids = {
        review["id"]
        for review in student_a_reviews
    }

    assert (
        review_a["review"]["id"]
        in student_a_review_ids
    )

    assert (
        review_b["review"]["id"]
        not in student_a_review_ids
    )

    assert all(
        review["student_id"]
        == str(student_a_id)
        for review in student_a_reviews
    )

    response_b = client.get(
        "/reviews/me",
        headers=auth_headers(token_b),
    )

    assert response_b.status_code == 200

    student_b_reviews = (
        response_b.json()
    )

    student_b_review_ids = {
        review["id"]
        for review in student_b_reviews
    }

    assert (
        review_b["review"]["id"]
        in student_b_review_ids
    )

    assert (
        review_a["review"]["id"]
        not in student_b_review_ids
    )

    assert all(
        review["student_id"]
        == str(student_b_id)
        for review in student_b_reviews
    )


def test_student_cannot_access_teacher_pending_queue(
    client,
):
    _, _, token = create_student_with_token(
        client
    )

    response = client.get(
        "/reviews/pending",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_student_cannot_access_teacher_review_detail(
    client,
):
    _, _, student_token = (
        create_student_with_token(
            client
        )
    )

    review = create_review(
        client,
        token=student_token,
        activity_reference_id=(
            f"detail-{uuid.uuid4().hex}"
        ),
    )

    review_id = review["review"]["id"]

    response = client.get(
        f"/reviews/{review_id}",
        headers=auth_headers(
            student_token
        ),
    )

    assert response.status_code == 403


def test_teacher_can_view_pending_queue_and_review_detail(
    client,
):
    _, _, student_token = (
        create_student_with_token(
            client
        )
    )

    review_result = create_review(
        client,
        token=student_token,
        activity_reference_id=(
            f"queue-{uuid.uuid4().hex}"
        ),
        question=(
            "Please review this ISL practice."
        ),
    )

    review_id = (
        review_result["review"]["id"]
    )

    (
        teacher_id,
        _,
        teacher_token,
    ) = create_teacher_with_token(
        client
    )

    # IMPORTANT:
    # Do not assume the newly created review is on
    # page 1. The local database can contain historical
    # pending reviews from previous test executions.
    queue_review = (
        get_pending_review_from_paginated_queue(
            client,
            teacher_token=teacher_token,
            review_id=review_id,
        )
    )

    assert queue_review is not None

    assert (
        queue_review["id"]
        == review_id
    )

    assert queue_review["status"] == "pending"

    detail_response = client.get(
        f"/reviews/{review_id}",
        headers=auth_headers(
            teacher_token
        ),
    )

    assert (
        detail_response.status_code
        == 200
    )

    detail = detail_response.json()

    assert detail["id"] == review_id

    assert detail["status"] == "pending"

    assert detail["reviewed_by"] is None

    assert (
        str(teacher_id)
        != detail["student_id"]
    )


def test_teacher_can_resolve_review(
    client,
):
    _, _, student_token = (
        create_student_with_token(
            client
        )
    )

    review_result = create_review(
        client,
        token=student_token,
        activity_reference_id=(
            f"resolve-{uuid.uuid4().hex}"
        ),
        question=(
            "I need a teacher to check "
            "this sign."
        ),
    )

    review_id = (
        review_result["review"]["id"]
    )

    (
        teacher_id,
        _,
        teacher_token,
    ) = create_teacher_with_token(
        client
    )

    response = client.patch(
        f"/reviews/{review_id}/resolve",
        headers=auth_headers(
            teacher_token
        ),
        json={
            "teacher_feedback": (
                "Please keep your hand upright "
                "and repeat the sign slowly."
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    resolved = response.json()

    assert resolved["id"] == review_id

    assert resolved["status"] == "reviewed"

    assert (
        resolved["teacher_feedback"]
        == (
            "Please keep your hand upright "
            "and repeat the sign slowly."
        )
    )

    assert (
        resolved["reviewed_by"]
        == str(teacher_id)
    )

    assert resolved["reviewed_at"] is not None


def test_review_cannot_be_resolved_twice(
    client,
):
    _, _, student_token = (
        create_student_with_token(
            client
        )
    )

    review_result = create_review(
        client,
        token=student_token,
        activity_reference_id=(
            f"twice-{uuid.uuid4().hex}"
        ),
    )

    review_id = (
        review_result["review"]["id"]
    )

    _, _, teacher_token = (
        create_teacher_with_token(
            client
        )
    )

    first_response = client.patch(
        f"/reviews/{review_id}/resolve",
        headers=auth_headers(
            teacher_token
        ),
        json={
            "teacher_feedback": (
                "First governed teacher review."
            ),
        },
    )

    assert first_response.status_code == 200

    second_response = client.patch(
        f"/reviews/{review_id}/resolve",
        headers=auth_headers(
            teacher_token
        ),
        json={
            "teacher_feedback": (
                "Second review must not overwrite "
                "the first review."
            ),
        },
    )

    assert second_response.status_code == 409


def test_teacher_cannot_supply_server_controlled_review_fields(
    client,
):
    _, _, student_token = (
        create_student_with_token(
            client
        )
    )

    review_result = create_review(
        client,
        token=student_token,
        activity_reference_id=(
            f"server-owned-{uuid.uuid4().hex}"
        ),
    )

    review_id = (
        review_result["review"]["id"]
    )

    _, _, teacher_token = (
        create_teacher_with_token(
            client
        )
    )

    response = client.patch(
        f"/reviews/{review_id}/resolve",
        headers=auth_headers(
            teacher_token
        ),
        json={
            "teacher_feedback": (
                "Valid teacher feedback."
            ),
            "status": "reviewed",
            "reviewed_by": str(
                uuid.uuid4()
            ),
            "reviewed_at": (
                "2026-01-01T00:00:00Z"
            ),
        },
    )

    assert response.status_code == 422


def test_teacher_get_unknown_review_returns_404(
    client,
):
    _, _, teacher_token = (
        create_teacher_with_token(
            client
        )
    )

    unknown_review_id = uuid.uuid4()

    response = client.get(
        f"/reviews/{unknown_review_id}",
        headers=auth_headers(
            teacher_token
        ),
    )

    assert response.status_code == 404


def test_teacher_resolve_unknown_review_returns_404(
    client,
):
    _, _, teacher_token = (
        create_teacher_with_token(
            client
        )
    )

    unknown_review_id = uuid.uuid4()

    response = client.patch(
        (
            f"/reviews/"
            f"{unknown_review_id}/resolve"
        ),
        headers=auth_headers(
            teacher_token
        ),
        json={
            "teacher_feedback": (
                "This review does not exist."
            ),
        },
    )

    assert response.status_code == 404


def test_database_role_change_is_enforced_after_login(
    client,
):
    (
        teacher_id,
        teacher_email,
        teacher_token,
    ) = create_teacher_with_token(
        client
    )

    initial_response = client.get(
        "/reviews/pending",
        headers=auth_headers(
            teacher_token
        ),
        params={
            "limit": 1,
            "offset": 0,
        },
    )

    assert initial_response.status_code == 200

    db = SessionLocal()

    try:
        teacher = (
            db.query(User)
            .filter(
                User.id == teacher_id
            )
            .one()
        )

        assert teacher.email == teacher_email

        teacher.role = "student"

        db.commit()
        db.refresh(teacher)

    finally:
        db.close()

    # The same JWT must no longer grant teacher
    # privileges because RBAC checks the current
    # persisted user record.
    response_after_role_change = client.get(
        "/reviews/pending",
        headers=auth_headers(
            teacher_token
        ),
        params={
            "limit": 1,
            "offset": 0,
        },
    )

    assert (
        response_after_role_change.status_code
        == 403
    )
