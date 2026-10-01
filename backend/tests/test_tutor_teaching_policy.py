import pytest

from app.ai.tutor.intent import TutorIntent
from app.ai.tutor.teaching_policy import (
    TeachingStrategy,
    TutorTeachingPolicy,
)


@pytest.mark.parametrize("intent", list(TutorIntent))
def test_every_tutor_intent_has_strategy(intent: TutorIntent):
    strategy = TutorTeachingPolicy.get_strategy(intent)

    assert isinstance(strategy, TeachingStrategy)
    assert strategy.intent == intent
    assert strategy.instruction.strip()
    assert strategy.preferred_structure


def test_explain_strategy_is_grounded():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.EXPLAIN
    )

    assert "provided" in strategy.instruction.lower()
    assert "evidence" in strategy.instruction.lower()


def test_example_strategy_requests_example():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.EXAMPLE
    )

    assert "example" in strategy.instruction.lower()
    assert "Example" in strategy.preferred_structure


def test_simplify_strategy_uses_plain_language():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.SIMPLIFY
    )

    assert "plain-language" in strategy.instruction


def test_practice_strategy_rejects_unsupported_concepts():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.PRACTICE
    )

    assert "absent from the evidence" in strategy.instruction


def test_quiz_strategy_requires_evidence():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.QUIZ
    )

    assert "provided evidence" in strategy.instruction


def test_learning_guidance_does_not_infer_disability():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.LEARNING_GUIDANCE
    )

    assert "disability" in strategy.instruction
    assert "not explicitly provided" in strategy.instruction


def test_invalid_intent_falls_back_to_general_qa():
    strategy = TutorTeachingPolicy.get_strategy(
        "unsupported"  # type: ignore[arg-type]
    )

    assert strategy.intent == TutorIntent.GENERAL_QA


def test_strategy_is_immutable():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.EXPLAIN
    )

    with pytest.raises(AttributeError):
        strategy.instruction = "override"  # type: ignore[misc]