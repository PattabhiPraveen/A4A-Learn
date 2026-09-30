import pytest

from app.rag.python_intent import (
    is_python_programming_query,
)


@pytest.mark.parametrize(
    "question",
    [
        "What is Python?",
        "Explain PYTHON loops",
        "python syntax for adding 3+5",
        "Explain PyThOn dictionaries",
        "How does Python pathlib work?",
        "PYTHON",
        "python",
    ],
)
def test_python_programming_intent_is_case_insensitive(
    question,
):
    assert (
        is_python_programming_query(question)
        is True
    )


@pytest.mark.parametrize(
    "question",
    [
        "",
        "   ",
        "Explain Java loops",
        "What is machine learning?",
        "pythonista",
        "pythonic",
        "Monty Python movie",
        "Tell me about Monty Python",
    ],
)
def test_non_python_programming_queries_are_not_matched(
    question,
):
    assert (
        is_python_programming_query(question)
        is False
    )