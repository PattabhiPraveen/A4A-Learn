import pytest

from app.rag.web.evidence_selector import (
    EvidenceSelector,
)
from app.rag.web.models import (
    FetchedWebDocument,
)


def make_document(
    content: str,
) -> FetchedWebDocument:
    return FetchedWebDocument(
        title="Python Documentation",
        url=(
            "https://docs.python.org/"
            "3/library/pathlib.html"
        ),
        domain="docs.python.org",
        content=content,
    )


def test_selector_preserves_short_document():
    content = (
        "Path.read_text reads the contents of a file "
        "as text."
    )

    result = EvidenceSelector.select(
        question=(
            "What does pathlib.Path.read_text do?"
        ),
        document=make_document(content),
    )

    assert result.content == content
    assert result.domain == "docs.python.org"


def test_selector_finds_relevant_content_after_first_5000():
    prefix = (
        "unrelated documentation "
        * 400
    )

    target = (
        "Path.read_text opens the file in text mode, "
        "reads its contents, and closes the file."
    )

    suffix = (
        " additional documentation"
        * 400
    )

    document = make_document(
        prefix
        + target
        + suffix
    )

    # Reproduce the exact failure mode we discovered:
    # the useful method documentation occurs after the
    # old 5,000-character prefix boundary.
    assert (
        "read_text"
        not in document.content[:5000]
    )

    result = EvidenceSelector.select(
        question=(
            "What does pathlib.Path.read_text do "
            "in Python?"
        ),
        document=document,
    )

    assert "Path.read_text" in result.content

    assert (
        len(result.content)
        <= EvidenceSelector.MAX_EVIDENCE_CHARS
    )


def test_selector_keeps_long_evidence_bounded():
    content = (
        ("general documentation " * 500)
        + (
            "Path.read_text reads textual file "
            "content. "
        )
        + ("additional documentation " * 500)
    )

    result = EvidenceSelector.select(
        question="Explain Path.read_text",
        document=make_document(content),
    )

    assert (
        len(result.content)
        <= 5000
    )

    assert (
        "read_text"
        in result.content
    )


def test_selector_extracts_qualified_identifier_terms():
    terms = EvidenceSelector._query_terms(
        "What does pathlib.Path.read_text do?"
    )

    assert "pathlib.path.read_text" in terms
    assert "pathlib" in terms
    assert "path" in terms
    assert "read_text" in terms


def test_selector_prefers_specific_longer_term():
    prefix = (
        "path is mentioned here "
        * 300
    )

    target = (
        "read_text is the relevant method "
        "for this learner question."
    )

    document = make_document(
        prefix
        + target
        + (" trailing documentation" * 300)
    )

    result = EvidenceSelector.select(
        question=(
            "What does Path.read_text do?"
        ),
        document=document,
    )

    assert (
        "read_text"
        in result.content
    )


def test_selector_uses_prefix_when_no_term_matches():
    content = (
        "A" * 7000
    )

    result = EvidenceSelector.select(
        question=(
            "completely unrelated query"
        ),
        document=make_document(content),
    )

    assert len(result.content) == 5000

    assert (
        result.content
        == content[:5000]
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
    document = make_document(
        "Path.read_text reads a file as text."
    )

    result = EvidenceSelector.select(
        question="Explain read_text",
        document=document,
    )

    assert (
        result.title
        == "Python Documentation"
    )

    assert (
        str(result.url)
        == (
            "https://docs.python.org/"
            "3/library/pathlib.html"
        )
    )

    assert (
        result.domain
        == "docs.python.org"
    )

    assert (
        len(result.content)
        <= 5000
    )