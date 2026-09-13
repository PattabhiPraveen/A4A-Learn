from dataclasses import dataclass
from enum import Enum


class EscalationDecision(str, Enum):
    CONTINUE = "continue"
    RETRY = "retry"
    REVIEW = "review"


class EscalationReason(str, Enum):
    NORMAL = "normal"
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_DIFFICULTY = "repeated_difficulty"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STUDENT_REQUESTED_HELP = "student_requested_help"
    CONSEQUENTIAL_DECISION = "consequential_decision"


@dataclass(frozen=True)
class EscalationResult:
    decision: EscalationDecision
    reason: EscalationReason
    requires_human_review: bool


class EscalationPolicy:
    """
    Deterministic runtime human-in-the-loop policy.

    The policy converts learning/AI signals into workflow decisions.
    It does not perform database operations and does not retrain models.

    Decision precedence:
        1. Consequential decision       -> REVIEW
        2. Explicit learner help        -> REVIEW
        3. Insufficient RAG evidence    -> REVIEW
        4. Repeated ISL difficulty      -> REVIEW
        5. Low-confidence ISL result    -> RETRY
        6. Otherwise                    -> CONTINUE
    """

    ISL_CONFIDENCE_THRESHOLD = 0.70
    ISL_REPEATED_ATTEMPT_THRESHOLD = 3
    ISL_WEAK_ACCURACY_THRESHOLD = 60.0

    @classmethod
    def evaluate(
        cls,
        *,
        activity_type: str,
        ai_confidence: float | None = None,
        sufficient_evidence: bool = True,
        student_requested_help: bool = False,
        consequential: bool = False,
        attempt_count: int = 0,
        accuracy_percent: float | None = None,
    ) -> EscalationResult:

        activity = activity_type.strip().lower()

        if consequential:
            return EscalationResult(
                decision=EscalationDecision.REVIEW,
                reason=EscalationReason.CONSEQUENTIAL_DECISION,
                requires_human_review=True,
            )

        if student_requested_help:
            return EscalationResult(
                decision=EscalationDecision.REVIEW,
                reason=EscalationReason.STUDENT_REQUESTED_HELP,
                requires_human_review=True,
            )

        if activity == "rag" and not sufficient_evidence:
            return EscalationResult(
                decision=EscalationDecision.REVIEW,
                reason=EscalationReason.INSUFFICIENT_EVIDENCE,
                requires_human_review=True,
            )

        if activity == "isl":
            if (
                attempt_count >= cls.ISL_REPEATED_ATTEMPT_THRESHOLD
                and accuracy_percent is not None
                and accuracy_percent < cls.ISL_WEAK_ACCURACY_THRESHOLD
            ):
                return EscalationResult(
                    decision=EscalationDecision.REVIEW,
                    reason=EscalationReason.REPEATED_DIFFICULTY,
                    requires_human_review=True,
                )

            if (
                ai_confidence is not None
                and ai_confidence < cls.ISL_CONFIDENCE_THRESHOLD
            ):
                return EscalationResult(
                    decision=EscalationDecision.RETRY,
                    reason=EscalationReason.LOW_CONFIDENCE,
                    requires_human_review=False,
                )

        return EscalationResult(
            decision=EscalationDecision.CONTINUE,
            reason=EscalationReason.NORMAL,
            requires_human_review=False,
        )
