import pytest

from app.ai.tutor.intent import TutorIntent
from app.ai.tutor.intent_classifier import TutorIntentClassifier


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Explain Python loops", TutorIntent.EXPLAIN),
        ("Teach me Python functions", TutorIntent.EXPLAIN),
        ("Help me understand machine learning", TutorIntent.EXPLAIN),

        ("Give me an example of a Python loop", TutorIntent.EXAMPLE),
        ("Show me an example of a function", TutorIntent.EXAMPLE),
        ("Explain Python loops with an example", TutorIntent.EXAMPLE),

        ("Explain this in simple terms", TutorIntent.SIMPLIFY),
        ("Can you explain simply?", TutorIntent.SIMPLIFY),
        ("Explain this in easy words", TutorIntent.SIMPLIFY),

        ("Give me a practice question", TutorIntent.PRACTICE),
        ("I want to practice Python loops", TutorIntent.PRACTICE),
        ("Give me some exercises on variables", TutorIntent.PRACTICE),

        ("Quiz me on Python", TutorIntent.QUIZ),
        ("Test me on machine learning", TutorIntent.QUIZ),
        ("Give me a quiz about loops", TutorIntent.QUIZ),

        ("Debug this code", TutorIntent.DEBUG),
        ("Fix my code", TutorIntent.DEBUG),
        ("What is wrong with this code?", TutorIntent.DEBUG),

        (
            "Compare lists and tuples",
            TutorIntent.COMPARE,
        ),
        (
            "What is the difference between AI and ML?",
            TutorIntent.COMPARE,
        ),
        ("Python lists vs tuples", TutorIntent.COMPARE),

        ("Summarize this lesson", TutorIntent.SUMMARIZE),
        ("Give me the key points", TutorIntent.SUMMARIZE),

        (
            "What should I learn next?",
            TutorIntent.LEARNING_GUIDANCE,
        ),
        (
            "Where should I start learning Python?",
            TutorIntent.LEARNING_GUIDANCE,
        ),
        (
            "Give me a study plan",
            TutorIntent.LEARNING_GUIDANCE,
        ),

        ("What is Python?", TutorIntent.GENERAL_QA),
        (
            "What is retrieval augmented generation?",
            TutorIntent.GENERAL_QA,
        ),
    ],
)
def test_tutor_intent_classification(
    question: str,
    expected: TutorIntent,
):
    assert TutorIntentClassifier.classify(question) == expected


@pytest.mark.parametrize(
    "question",
    [
        "",
        "   ",
        "\n\t",
    ],
)
def test_empty_question_defaults_to_general_qa(question: str):
    assert (
        TutorIntentClassifier.classify(question)
        == TutorIntent.GENERAL_QA
    )


def test_none_like_non_string_input_defaults_safely():
    assert (
        TutorIntentClassifier.classify(None)  # type: ignore[arg-type]
        == TutorIntent.GENERAL_QA
    )


def test_classification_is_case_insensitive():
    assert (
        TutorIntentClassifier.classify(
            "QUIZ ME ON PYTHON LOOPS"
        )
        == TutorIntent.QUIZ
    )


def test_quiz_has_priority_over_general_explanation():
    assert (
        TutorIntentClassifier.classify(
            "Explain Python loops and then quiz me"
        )
        == TutorIntent.QUIZ
    )


def test_example_has_priority_over_explain():
    assert (
        TutorIntentClassifier.classify(
            "Explain Python loops with an example"
        )
        == TutorIntent.EXAMPLE
    )