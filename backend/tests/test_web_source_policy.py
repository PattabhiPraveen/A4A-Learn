from app.rag.web.models import (
    WebSearchResult,
)
from app.rag.web.source_policy import (
    WebSourcePolicy,
)
from app.rag.web.web_retriever import (
    WebRetriever,
)


def make_result(
    url: str,
    title: str = "Test source",
    snippet: str = "Trusted learning content.",
) -> WebSearchResult:
    return WebSearchResult(
        title=title,
        url=url,
        snippet=snippet,
    )


def test_exact_domain_is_allowed():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    assert policy.is_allowed(
        "https://docs.python.org/3/tutorial/"
    )


def test_subdomain_is_allowed():
    policy = WebSourcePolicy(
        "python.org"
    )

    assert policy.is_allowed(
        "https://docs.python.org/3/"
    )


def test_untrusted_domain_is_rejected():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    assert not policy.is_allowed(
        "https://example.com/python"
    )


def test_domain_suffix_attack_is_rejected():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    assert not policy.is_allowed(
        "https://docs.python.org.attacker.com/"
    )


def test_similar_domain_is_rejected():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    assert not policy.is_allowed(
        "https://fake-docs.python.org.example.com/"
    )


def test_approved_result_becomes_trusted_evidence():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    result = make_result(
        "https://docs.python.org/3/tutorial/"
    )

    evidence = policy.approve(
        result
    )

    assert evidence is not None
    assert evidence.domain == (
        "docs.python.org"
    )
    assert evidence.content == (
        "Trusted learning content."
    )


def test_unapproved_result_is_not_trusted():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    result = make_result(
        "https://example.com/python"
    )

    assert policy.approve(
        result
    ) is None


def test_retriever_filters_untrusted_results():
    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = [
        make_result(
            "https://example.com/python"
        ),
        make_result(
            "https://docs.python.org/3/tutorial/"
        ),
    ]

    approved = (
        retriever.filter_results(
            results
        )
    )

    assert len(approved) == 1
    assert approved[0].domain == (
        "docs.python.org"
    )