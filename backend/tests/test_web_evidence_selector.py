import pytest

from app.rag.web.evidence_selector import EvidenceSelector
from app.rag.web.models import FetchedWebDocument


def make_document(
    content: str,
    *,
    title: str = "Python Documentation",
    url: str = "https://docs.python.org/3/tutorial/",
    domain: str = "docs.python.org",
) -> FetchedWebDocument:
    return FetchedWebDocument(
        title=title,
        url=url,
        domain=domain,
        content=content,
    )


def test_selector_preserves_short_document():
    content = (
        "Python is an interpreted programming language."
    )

    result = EvidenceSelector.select(
        question="What is Python?",
        document=make_document(content),
    )

    assert result.content == content


def test_selector_finds_relevant_content_after_first_5000():
    content = (
        "A" * 6000
        + " Python is an interpreted programming language."
    )

    result = EvidenceSelector.select(
        question="What is Python?",
        document=make_document(content),
    )

    assert "Python" in result.content
    assert len(result.content) <= 5000


def test_selector_keeps_long_evidence_bounded():
    content = (
        "Python is an interpreted programming language. "
        * 1000
    )

    result = EvidenceSelector.select(
        question="What is Python?",
        document=make_document(content),
    )

    assert len(result.content) <= 5000


def test_selector_extracts_qualified_identifier_terms():
    content = (
        "FastAPI provides an API framework for Python."
    )

    result = EvidenceSelector.select(
        question="What is FastAPI?",
        document=make_document(content),
    )

    assert "FastAPI" in result.content


def test_selector_prefers_specific_longer_term():
    content = (
        "Python is a language. "
        "Python programming language supports "
        "dynamic typing."
    )

    result = EvidenceSelector.select(
        question="Python programming language",
        document=make_document(content),
    )

    assert "Python programming language" in result.content


def test_selector_rejects_when_no_term_matches():
    content = (
        "A" * 7000
    )

    with pytest.raises(
        ValueError,
        match="No query-relevant external evidence",
    ):
        EvidenceSelector.select(
            question=(
                "completely unrelated query"
            ),
            document=make_document(content),
        )


def test_selector_rejects_empty_question():
    document = make_document(
        "Python documentation."
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        EvidenceSelector.select(
            question="   ",
            document=document,
        )


def test_selector_returns_trusted_bounded_evidence():
    content = (
        "Python supports functions and classes."
    )

    result = EvidenceSelector.select(
        question="What does Python support?",
        document=make_document(content),
    )

    assert result.title == "Python Documentation"
    assert result.domain == "docs.python.org"
    assert str(result.url) == (
        "https://docs.python.org/3/tutorial/"
    )
    assert result.content
    assert len(result.content) <= 5000


def test_select_rejects_document_with_no_query_relevance():
    document = FetchedWebDocument(
        title="Python Documentation",
        url="https://docs.python.org/3/tutorial/",
        domain="docs.python.org",
        content=(
            "This page explains database administration, "
            "network routing, storage arrays and backup systems."
        ),
    )

    with pytest.raises(
        ValueError,
        match="No query-relevant external evidence",
    ):
        EvidenceSelector.select(
            question="What is Python?",
            document=document,
        )


def test_select_accepts_document_with_query_relevance():
    document = FetchedWebDocument(
        title="Python Documentation",
        url="https://docs.python.org/3/tutorial/",
        domain="docs.python.org",
        content=(
            "Python is an interpreted programming language "
            "with dynamic semantics."
        ),
    )

    result = EvidenceSelector.select(
        question="What is Python?",
        document=document,
    )

    assert result.title == "Python Documentation"
    assert result.domain == "docs.python.org"
    assert "Python" in result.content


def test_select_does_not_accept_long_unrelated_document():
    document = FetchedWebDocument(
        title="Unrelated Documentation",
        url="https://docs.python.org/3/tutorial/",
        domain="docs.python.org",
        content=(
            "Database administration and network routing. "
            * 500
        ),
    )

    with pytest.raises(
        ValueError,
        match="No query-relevant external evidence",
    ):
        EvidenceSelector.select(
            question="What is Python?",
            document=document,
        )