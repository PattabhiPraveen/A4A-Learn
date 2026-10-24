from app.rag.web.orchestrator import WebEvidenceOrchestrator as O


def test_supported_claim():
    assert O._claim_has_lexical_support(
        "Python supports list comprehensions.",
        "Python supports list comprehensions.",
    )


def test_unrelated_claim_rejected():
    assert not O._claim_has_lexical_support(
        "Python supports underwater spacecraft.",
        "Python supports list comprehensions.",
    )


def test_correct_numeric_answer():
    assert O._claim_has_lexical_support(
        "8",
        "The result is 8.",
    )


def test_unsupported_extra_number():
    assert not O._claim_has_lexical_support(
        "The results are 8 and 99.",
        "The result is 8.",
    )
