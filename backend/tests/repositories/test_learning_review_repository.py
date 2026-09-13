import uuid

from app.models.learning_review import LearningReview
from app.repositories.learning_review_repository import LearningReviewRepository


def test_learning_review_repository_import():
    assert LearningReviewRepository is not None


def test_learning_review_model_table_name():
    assert LearningReview.__tablename__ == "learning_reviews"


def test_learning_review_model_has_expected_columns():
    expected_columns = {
        "id",
        "student_id",
        "activity_type",
        "activity_reference_id",
        "question_or_activity",
        "ai_response",
        "retrieved_sources",
        "ai_confidence",
        "reason_for_escalation",
        "student_attempts",
        "status",
        "teacher_feedback",
        "reviewed_by",
        "created_at",
        "reviewed_at",
    }

    actual_columns = set(LearningReview.__table__.columns.keys())

    assert expected_columns == actual_columns


def test_learning_review_default_status():
    status_column = LearningReview.__table__.columns["status"]

    assert status_column.server_default is not None
    assert "pending" in str(status_column.server_default.arg)


def test_repository_exposes_required_operations():
    required_operations = {
        "create",
        "get_by_id",
        "list_by_student",
        "list_pending",
        "count_pending",
        "count_pending_by_student",
        "find_pending_for_activity",
        "save",
    }

    for operation in required_operations:
        assert hasattr(LearningReviewRepository, operation)


def test_random_review_id_is_uuid():
    review_id = uuid.uuid4()

    assert isinstance(review_id, uuid.UUID)
