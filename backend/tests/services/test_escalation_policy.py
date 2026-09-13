import pytest

from app.services.escalation_policy import (
    EscalationDecision,
    EscalationPolicy,
    EscalationReason,
)


def test_normal_isl_interaction_continues():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.90,
        attempt_count=1,
        accuracy_percent=100.0,
    )

    assert result.decision == EscalationDecision.CONTINUE
    assert result.reason == EscalationReason.NORMAL
    assert result.requires_human_review is False


def test_low_confidence_isl_requests_retry():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.69,
        attempt_count=1,
        accuracy_percent=0.0,
    )

    assert result.decision == EscalationDecision.RETRY
    assert result.reason == EscalationReason.LOW_CONFIDENCE
    assert result.requires_human_review is False


def test_exact_confidence_threshold_does_not_retry():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.70,
        attempt_count=1,
        accuracy_percent=100.0,
    )

    assert result.decision == EscalationDecision.CONTINUE


def test_repeated_isl_difficulty_requires_review():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.90,
        attempt_count=3,
        accuracy_percent=50.0,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == EscalationReason.REPEATED_DIFFICULTY
    assert result.requires_human_review is True


def test_exact_60_percent_is_not_weak():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.90,
        attempt_count=3,
        accuracy_percent=60.0,
    )

    assert result.decision == EscalationDecision.CONTINUE


def test_two_attempts_do_not_trigger_repeated_difficulty():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.90,
        attempt_count=2,
        accuracy_percent=0.0,
    )

    assert result.decision == EscalationDecision.CONTINUE


def test_insufficient_rag_evidence_requires_review():
    result = EscalationPolicy.evaluate(
        activity_type="rag",
        sufficient_evidence=False,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == EscalationReason.INSUFFICIENT_EVIDENCE
    assert result.requires_human_review is True


def test_sufficient_rag_evidence_continues():
    result = EscalationPolicy.evaluate(
        activity_type="rag",
        sufficient_evidence=True,
    )

    assert result.decision == EscalationDecision.CONTINUE
    assert result.requires_human_review is False


def test_explicit_student_help_always_requires_review():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.99,
        student_requested_help=True,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == EscalationReason.STUDENT_REQUESTED_HELP
    assert result.requires_human_review is True


def test_consequential_decision_always_requires_review():
    result = EscalationPolicy.evaluate(
        activity_type="rag",
        ai_confidence=0.99,
        sufficient_evidence=True,
        consequential=True,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == EscalationReason.CONSEQUENTIAL_DECISION


def test_repeated_difficulty_takes_precedence_over_low_confidence():
    result = EscalationPolicy.evaluate(
        activity_type="isl",
        ai_confidence=0.40,
        attempt_count=4,
        accuracy_percent=25.0,
    )

    assert result.decision == EscalationDecision.REVIEW
    assert result.reason == EscalationReason.REPEATED_DIFFICULTY


@pytest.mark.parametrize(
    "activity_type",
    [
        "ISL",
        "isl",
        " ISL ",
    ],
)
def test_activity_type_is_normalized(activity_type):
    result = EscalationPolicy.evaluate(
        activity_type=activity_type,
        ai_confidence=0.50,
        attempt_count=1,
    )

    assert result.decision == EscalationDecision.RETRY
