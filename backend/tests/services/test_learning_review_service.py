import uuid
from unittest.mock import MagicMock

import pytest

from app.services.escalation_policy import EscalationDecision
from app.services.learning_review_service import LearningReviewService


@pytest.fixture
def service():
    db = MagicMock()
    svc = LearningReviewService(db)
    svc.repository = MagicMock()
    return svc, db


def test_continue_does_not_create_review(service):
    svc, db = service

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="isl",
        question_or_activity="Practice letter A",
        ai_confidence=0.95,
        attempt_count=1,
        accuracy_percent=100.0,
    )

    assert result.decision == EscalationDecision.CONTINUE
    assert result.requires_human_review is False
    assert result.review is None
    assert result.created is False

    svc.repository.create.assert_not_called()
    db.commit.assert_not_called()


def test_retry_does_not_create_review(service):
    svc, db = service

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="isl",
        question_or_activity="Practice letter A",
        ai_confidence=0.50,
        attempt_count=1,
        accuracy_percent=0.0,
    )

    assert result.decision == EscalationDecision.RETRY
    assert result.requires_human_review is False
    assert result.review is None
    assert result.created is False

    svc.repository.create.assert_not_called()
    db.commit.assert_not_called()


def test_review_creates_pending_review(service):
    svc, db = service
    student_id = uuid.uuid4()
    review = MagicMock()

    svc.repository.find_pending_for_activity.return_value = None
    svc.repository.create.return_value = review

    result = svc.evaluate_and_escalate(
        student_id=student_id,
        activity_type="ISL",
        activity_reference_id="letter-A",
        question_or_activity="Practice letter A",
        ai_confidence=0.40,
        attempt_count=4,
        accuracy_percent=25.0,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.requires_human_review is True
    assert result.review is review
    assert result.created is True
    assert result.reason == "repeated_difficulty"

    svc.repository.create.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(review)


def test_duplicate_pending_review_is_reused(service):
    svc, db = service
    existing_review = MagicMock()

    svc.repository.find_pending_for_activity.return_value = existing_review

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="rag",
        activity_reference_id="question-001",
        question_or_activity="Explain photosynthesis",
        sufficient_evidence=False,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.review is existing_review
    assert result.created is False

    svc.repository.create.assert_not_called()
    db.commit.assert_not_called()


def test_review_without_reference_can_be_created(service):
    svc, db = service
    review = MagicMock()

    svc.repository.create.return_value = review

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="rag",
        question_or_activity="Explain an unsupported topic",
        sufficient_evidence=False,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.created is True

    svc.repository.find_pending_for_activity.assert_not_called()
    svc.repository.create.assert_called_once()
    db.commit.assert_called_once()


def test_student_requested_help_creates_review(service):
    svc, db = service
    review = MagicMock()

    svc.repository.create.return_value = review

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="isl",
        question_or_activity="I need help with letter D",
        student_requested_help=True,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == "student_requested_help"
    assert result.created is True

    db.commit.assert_called_once()


def test_consequential_activity_creates_review(service):
    svc, db = service
    review = MagicMock()

    svc.repository.create.return_value = review

    result = svc.evaluate_and_escalate(
        student_id=uuid.uuid4(),
        activity_type="learning",
        question_or_activity="Change learner intervention",
        consequential=True,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == "consequential_decision"
    assert result.created is True

    db.commit.assert_called_once()


def test_transaction_rolls_back_on_repository_failure(service):
    svc, db = service

    svc.repository.create.side_effect = RuntimeError("database failure")

    with pytest.raises(RuntimeError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="rag",
            question_or_activity="Unsupported question",
            sufficient_evidence=False,
        )

    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_empty_activity_type_rejected(service):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="   ",
            question_or_activity="Activity",
        )


def test_empty_question_rejected(service):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="isl",
            question_or_activity="   ",
        )


def test_invalid_confidence_rejected(service):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="isl",
            question_or_activity="Practice A",
            ai_confidence=1.1,
        )


def test_negative_attempt_count_rejected(service):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="isl",
            question_or_activity="Practice A",
            attempt_count=-1,
        )


def test_invalid_accuracy_rejected(service):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.evaluate_and_escalate(
            student_id=uuid.uuid4(),
            activity_type="isl",
            question_or_activity="Practice A",
            accuracy_percent=101.0,
        )


def test_get_student_reviews_is_scoped_to_student(service):
    svc, _ = service
    student_id = uuid.uuid4()

    expected = [MagicMock(), MagicMock()]
    svc.repository.list_by_student.return_value = expected

    result = svc.get_student_reviews(
        student_id=student_id,
        limit=20,
        offset=5,
    )

    assert result == expected

    svc.repository.list_by_student.assert_called_once_with(
        student_id=student_id,
        limit=20,
        offset=5,
    )


def test_get_pending_reviews(service):
    svc, _ = service

    expected = [MagicMock(), MagicMock()]
    svc.repository.list_pending.return_value = expected

    result = svc.get_pending_reviews(
        limit=25,
        offset=0,
    )

    assert result == expected

    svc.repository.list_pending.assert_called_once_with(
        limit=25,
        offset=0,
    )


def test_get_review_by_id(service):
    svc, _ = service
    review_id = uuid.uuid4()
    review = MagicMock()

    svc.repository.get_by_id.return_value = review

    result = svc.get_review(
        review_id=review_id,
    )

    assert result is review

    svc.repository.get_by_id.assert_called_once_with(
        review_id
    )


def test_resolve_pending_review(service):
    svc, db = service

    review_id = uuid.uuid4()
    teacher_id = uuid.uuid4()

    review = MagicMock()
    review.status = "pending"

    svc.repository.get_by_id.return_value = review
    svc.repository.save.return_value = review

    result = svc.resolve_review(
        review_id=review_id,
        teacher_id=teacher_id,
        teacher_feedback="Please review the hand position.",
    )

    assert result is review

    assert review.status == "reviewed"
    assert review.teacher_feedback == (
        "Please review the hand position."
    )
    assert review.reviewed_by == teacher_id
    assert review.reviewed_at is not None

    svc.repository.save.assert_called_once_with(review)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(review)


def test_resolve_unknown_review_rejected(service):
    svc, db = service

    svc.repository.get_by_id.return_value = None

    with pytest.raises(
        LookupError,
        match="Learning review not found",
    ):
        svc.resolve_review(
            review_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            teacher_feedback="Teacher feedback",
        )

    svc.repository.save.assert_not_called()
    db.commit.assert_not_called()


def test_resolve_already_reviewed_rejected(service):
    svc, db = service

    review = MagicMock()
    review.status = "reviewed"

    svc.repository.get_by_id.return_value = review

    with pytest.raises(
        ValueError,
        match="Learning review is not pending",
    ):
        svc.resolve_review(
            review_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            teacher_feedback="Second review",
        )

    svc.repository.save.assert_not_called()
    db.commit.assert_not_called()


def test_resolve_blank_feedback_rejected(service):
    svc, db = service

    with pytest.raises(
        ValueError,
        match="teacher_feedback must not be empty",
    ):
        svc.resolve_review(
            review_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            teacher_feedback="   ",
        )

    svc.repository.get_by_id.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize(
    "limit,offset",
    [
        (0, 0),
        (101, 0),
        (10, -1),
    ],
)
def test_invalid_review_pagination_rejected(
    service,
    limit,
    offset,
):
    svc, _ = service

    with pytest.raises(ValueError):
        svc.get_student_reviews(
            student_id=uuid.uuid4(),
            limit=limit,
            offset=offset,
        )
