"""Python-programming intent detection for governed RAG routing."""

import re


_PYTHON_WORD_PATTERN = re.compile(
    r"\bpython\b",
    re.IGNORECASE,
)

_PROGRAMMING_TERMS = {
    "api",
    "class",
    "code",
    "coding",
    "decorator",
    "decorators",
    "dictionary",
    "dictionaries",
    "function",
    "functions",
    "import",
    "library",
    "libraries",
    "list",
    "lists",
    "loop",
    "loops",
    "module",
    "modules",
    "package",
    "packages",
    "pathlib",
    "program",
    "programming",
    "script",
    "syntax",
    "tuple",
    "tuples",
    "variable",
    "variables",
}

_NON_PROGRAMMING_PHRASES = {
    "monty python",
}


def is_python_programming_query(
    question: str,
) -> bool:
    """
    Return True when a question expresses Python-programming intent.

    Matching is case-insensitive and requires the standalone word
    'python'. Known non-programming uses are excluded.

    A question containing only Python itself, such as
    'What is Python?', is treated as programming intent because
    A4A Learn is a technical-learning platform.
    """

    normalized = " ".join(
        question.strip().lower().split()
    )

    if not normalized:
        return False

    if not _PYTHON_WORD_PATTERN.search(
        normalized
    ):
        return False

    if any(
        phrase in normalized
        for phrase in _NON_PROGRAMMING_PHRASES
    ):
        return False

    if normalized in {
        "python",
        "what is python",
        "what is python?",
        "explain python",
        "explain python.",
    }:
        return True

    words = set(
        re.findall(
            r"[a-z0-9_]+",
            normalized,
        )
    )

    if words & _PROGRAMMING_TERMS:
        return True

    # In the A4A Learn technical-learning context, a standalone
    # Python reference is treated as Python-programming intent
    # unless explicitly excluded above.
    return True