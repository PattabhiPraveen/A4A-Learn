import pytest

from app.ai.tutor.intent import TutorIntent
from app.ai.tutor.teaching_policy import TutorTeachingPolicy
from app.rag.generation.prompt_builder import (
    FALLBACK_MESSAGE,
    build_grounded_prompt,
)


def test_prompt_remains_backward_compatible():
    prompt = build_grounded_prompt(
        question="What is Python?",
        context="[Source 1]\nPython is a programming language.",
    )

    assert "What is Python?" in prompt
    assert "Python is a programming language." in prompt
    assert "TEACHING STRATEGY" not in prompt


def test_example_strategy_is_added_to_prompt():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.EXAMPLE
    )

    prompt = build_grounded_prompt(
        question="Give me an example of a Python loop.",
        context="[Source 1]\nA loop repeats instructions.",
        teaching_strategy=strategy,
    )

    assert "TEACHING STRATEGY" in prompt
    assert "Intent: example" in prompt
    assert "Example" in prompt
    assert "Why it works" in prompt


def test_simplify_strategy_is_added_to_prompt():
    strategy = TutorTeachingPolicy.get_strategy(
        TutorIntent.SIMPLIFY
    )

    prompt = build_grounded_prompt(
        question="Explain this in simple terms.",
        context="[Source 1]\nPython uses variables.",
        teaching_strategy=strategy,
    )

    assert "Intent: simplify" in prompt
    assert "Simple explanation" in prompt
    assert "Remember" in prompt


def test_accessibility_policy_does_not_require_audio():
    prompt = build_grounded_prompt(
        question="Explain Python.",
        context="[Source 1]\nPython is a programming language.",
    )

    assert "Do not require audio" in prompt
    assert "spoken instructions" in prompt


def test_prompt_contains_isl_non_invention_guardrail():
    prompt = build_grounded_prompt(
        question="How do I sign Python in ISL?",
        context="[Source 1]\nThis lesson discusses Python.",
    )

    assert "never invent, describe" in prompt
    assert "validated ISL learning content" in prompt


def test_fallback_contract_is_preserved():
    prompt = build_grounded_prompt(
        question="What is Python?",
        context="[Source 1]\nPython is a programming language.",
    )

    assert FALLBACK_MESSAGE in prompt


@pytest.mark.parametrize(
    "question,context",
    [
        ("", "Valid context"),
        ("   ", "Valid context"),
        ("Valid question", ""),
        ("Valid question", "   "),
    ],
)
def test_prompt_rejects_empty_required_input(
    question,
    context,
):
    with pytest.raises(ValueError):
        build_grounded_prompt(
            question=question,
            context=context,
        )