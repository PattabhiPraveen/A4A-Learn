import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.learning_review import LearningReview
from app.repositories.learning_review_repository import LearningReviewRepository
from app.services.escalation_policy import (
    EscalationDecision,
    EscalationPolicy,
    EscalationResult,
)


@dataclass(frozen=True)
class ReviewWorkflowResult:
    decision: EscalationDecision
    reason: str
    requires_human_review: bool
    review: LearningReview | None
    created: bool


class LearningReviewService:
    """
    Coordinates deterministic escalation policy with HITL persistence.

    Responsibilities:
    - evaluate governed escalation rules
    - create teacher-review records only when REVIEW is required
    - avoid duplicate pending reviews for the same referenced activity
    - provide learner-scoped review retrieval
    - provide teacher pending-review retrieval
    - resolve pending reviews with human accountability metadata
    - own commit/rollback transaction boundaries

    Teacher feedback is governed evidence and is not used for
    automatic model retraining.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = LearningReviewRepository(db)

    def evaluate_and_escalate(
        self,
        *,
        student_id: uuid.UUID,
        activity_type: str,
        question_or_activity: str,
        activity_reference_id: str | None = None,
        ai_response: str | None = None,
        retrieved_sources: str | None = None,
        ai_confidence: float | None = None,
        sufficient_evidence: bool = True,
        student_requested_help: bool = False,
        consequential: bool = False,
        attempt_count: int = 0,
        accuracy_percent: float | None = None,
    ) -> ReviewWorkflowResult:

        normalized_activity = self._normalize_activity_type(activity_type)

        question = self._require_text(
            question_or_activity,
            "question_or_activity",
        )

        self._validate_confidence(ai_confidence)
        self._validate_attempt_count(attempt_count)
        self._validate_accuracy(accuracy_percent)

        policy_result = EscalationPolicy.evaluate(
            activity_type=normalized_activity,
            ai_confidence=ai_confidence,
            sufficient_evidence=sufficient_evidence,
            student_requested_help=student_requested_help,
            consequential=consequential,
            attempt_count=attempt_count,
            accuracy_percent=accuracy_percent,
        )

        if policy_result.decision != EscalationDecision.REVIEW:
            return self._workflow_result(
                policy_result=policy_result,
                review=None,
                created=False,
            )

        normalized_reference = self._normalize_optional_text(
            activity_reference_id
        )

        if normalized_reference is not None:
            existing = self.repository.find_pending_for_activity(
                student_id=student_id,
                activity_type=normalized_activity,
                activity_reference_id=normalized_reference,
            )

            if existing is not None:
                return self._workflow_result(
                    policy_result=policy_result,
                    review=existing,
                    created=False,
                )

        try:
            review = self.repository.create(
                student_id=student_id,
                activity_type=normalized_activity,
                activity_reference_id=normalized_reference,
                question_or_activity=question,
                ai_response=self._normalize_optional_text(ai_response),
                retrieved_sources=self._normalize_optional_text(
                    retrieved_sources
                ),
                ai_confidence=ai_confidence,
                reason_for_escalation=policy_result.reason.value,
                student_attempts=attempt_count,
            )

            self.db.commit()
            self.db.refresh(review)

            return self._workflow_result(
                policy_result=policy_result,
                review=review,
                created=True,
            )

        except Exception:
            self.db.rollback()
            raise

    def get_student_reviews(
        self,
        *,
        student_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LearningReview]:
        """
        Return reviews belonging only to the supplied learner.

        The API must derive student_id from the authenticated user.
        """

        self._validate_pagination(
            limit=limit,
            offset=offset,
        )

        return self.repository.list_by_student(
            student_id=student_id,
            limit=limit,
            offset=offset,
        )

    def get_pending_reviews(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LearningReview]:
        """
        Return the teacher review queue.

        Teacher authorization is enforced at the API/RBAC boundary.
        """

        self._validate_pagination(
            limit=limit,
            offset=offset,
        )

        return self.repository.list_pending(
            limit=limit,
            offset=offset,
        )

    def get_review(
        self,
        *,
        review_id: uuid.UUID,
    ) -> LearningReview | None:
        """
        Retrieve a review by identifier.

        Authorization governing who may call this operation belongs
        at the API boundary.
        """

        return self.repository.get_by_id(review_id)

    def resolve_review(
        self,
        *,
        review_id: uuid.UUID,
        teacher_id: uuid.UUID,
        teacher_feedback: str,
    ) -> LearningReview:
        """
        Resolve a pending review.

        Human accountability fields are controlled by the backend:
        - status
        - teacher_feedback
        - reviewed_by
        - reviewed_at

        A review can be resolved only once.
        """

        feedback = self._require_text(
            teacher_feedback,
            "teacher_feedback",
        )

        review = self.repository.get_by_id(review_id)

        if review is None:
            raise LookupError("Learning review not found")

        normalized_status = (review.status or "").strip().lower()

        if normalized_status != "pending":
            raise ValueError("Learning review is not pending")

        try:
            review.status = "reviewed"
            review.teacher_feedback = feedback
            review.reviewed_by = teacher_id
            review.reviewed_at = datetime.now(timezone.utc)

            saved_review = self.repository.save(review)

            self.db.commit()
            self.db.refresh(saved_review)

            return saved_review

        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _workflow_result(
        *,
        policy_result: EscalationResult,
        review: LearningReview | None,
        created: bool,
    ) -> ReviewWorkflowResult:
        return ReviewWorkflowResult(
            decision=policy_result.decision,
            reason=policy_result.reason.value,
            requires_human_review=policy_result.requires_human_review,
            review=review,
            created=created,
        )

    @staticmethod
    def _normalize_activity_type(activity_type: str) -> str:
        if not isinstance(activity_type, str):
            raise ValueError("activity_type must be a string")

        value = activity_type.strip().lower()

        if not value:
            raise ValueError("activity_type must not be empty")

        return value

    @staticmethod
    def _require_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError("optional text values must be strings")

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _validate_confidence(
        value: float | None,
    ) -> None:
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError(
                "ai_confidence must be between 0.0 and 1.0"
            )

    @staticmethod
    def _validate_attempt_count(
        value: int,
    ) -> None:
        if value < 0:
            raise ValueError("attempt_count must be >= 0")

    @staticmethod
    def _validate_accuracy(
        value: float | None,
    ) -> None:
        if value is not None and not 0.0 <= value <= 100.0:
            raise ValueError(
                "accuracy_percent must be between 0.0 and 100.0"
            )

    @staticmethod
    def _validate_pagination(
        *,
        limit: int,
        offset: int,
    ) -> None:
        if limit < 1 or limit > 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        if offset < 0:
            raise ValueError(
                "offset must be >= 0"
            )
