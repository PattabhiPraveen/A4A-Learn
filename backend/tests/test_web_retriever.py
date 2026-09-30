import httpx
import pytest

from app.rag.web.models import (
    TrustedWebEvidence,
    WebSearchResult,
)
from app.rag.web.source_policy import (
    WebSourcePolicy,
)
from app.rag.web.web_retriever import (
    WebRetrievalDisabledError,
    WebRetrievalProviderError,
    WebRetriever,
)


class FakeResponse:
    def __init__(
        self,
        payload,
        *,
        status_code=200,
    ):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request(
                "GET",
                "http://127.0.0.1:8088/search",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "Simulated HTTP failure.",
                request=request,
                response=response,
            )


def test_filter_results_keeps_only_allowed_domains():
    policy = WebSourcePolicy(
        "docs.python.org,pytorch.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = [
        WebSearchResult(
            title="Python Documentation",
            url=(
                "https://docs.python.org/"
                "3/tutorial/"
            ),
            snippet=(
                "Official Python tutorial."
            ),
        ),
        WebSearchResult(
            title="Untrusted Result",
            url=(
                "https://example.com/python"
            ),
            snippet=(
                "Untrusted Python content."
            ),
        ),
        WebSearchResult(
            title="PyTorch Documentation",
            url=(
                "https://docs.pytorch.org/"
                "docs/stable/index.html"
            ),
            snippet=(
                "Official PyTorch documentation."
            ),
        ),
    ]

    approved = retriever.filter_results(
        results
    )

    assert len(approved) == 2

    assert all(
        isinstance(
            item,
            TrustedWebEvidence,
        )
        for item in approved
    )

    assert [
        item.domain
        for item in approved
    ] == [
        "docs.python.org",
        "docs.pytorch.org",
    ]


def test_filter_results_respects_max_results(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_MAX_RESULTS"
        ),
        1,
    )

    policy = WebSourcePolicy(
        "docs.python.org,pytorch.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = [
        WebSearchResult(
            title="Python Documentation",
            url=(
                "https://docs.python.org/"
                "3/tutorial/"
            ),
            snippet="Python tutorial.",
        ),
        WebSearchResult(
            title="PyTorch Documentation",
            url=(
                "https://docs.pytorch.org/"
                "docs/stable/index.html"
            ),
            snippet="PyTorch documentation.",
        ),
    ]

    approved = retriever.filter_results(
        results
    )

    assert len(approved) == 1

    assert (
        approved[0].domain
        == "docs.python.org"
    )


def test_search_requires_feature_flag(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        False,
    )

    retriever = WebRetriever()

    with pytest.raises(
        WebRetrievalDisabledError
    ):
        retriever.search(
            "What is Python?"
        )


def test_search_rejects_empty_question(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        True,
    )

    retriever = WebRetriever()

    with pytest.raises(
        ValueError
    ):
        retriever.search(
            "   "
        )


def test_search_parses_searxng_results(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        True,
    )

    def fake_get(
        url,
        params,
        timeout,
    ):
        assert (
            url
            == "http://127.0.0.1:8088/search"
        )

        assert (
            params["q"]
            == "machine learning"
        )

        assert (
            params["format"]
            == "json"
        )

        return FakeResponse(
            {
                "results": [
                    {
                        "title": (
                            "Scikit-learn"
                        ),
                        "url": (
                            "https://"
                            "scikit-learn.org/"
                            "stable/"
                        ),
                        "content": (
                            "Machine learning "
                            "documentation."
                        ),
                    },
                    {
                        "title": (
                            "Untrusted"
                        ),
                        "url": (
                            "https://example.com/"
                        ),
                        "content": (
                            "Untrusted content."
                        ),
                    },
                ]
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    policy = WebSourcePolicy(
        "scikit-learn.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "machine learning"
    )

    assert len(results) == 1

    assert (
        results[0].domain
        == "scikit-learn.org"
    )

    assert (
        results[0].title
        == "Scikit-learn"
    )


def test_search_ignores_malformed_provider_results(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        True,
    )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [
                    None,
                    "invalid",
                    {},
                    {
                        "title": "",
                        "url": (
                            "https://"
                            "docs.python.org/3/"
                        ),
                        "content": "Missing title.",
                    },
                    {
                        "title": "Missing URL",
                        "url": "",
                        "content": "Content.",
                    },
                    {
                        "title": "Missing Content",
                        "url": (
                            "https://"
                            "docs.python.org/3/"
                        ),
                        "content": "",
                    },
                    {
                        "title": (
                            "Python Documentation"
                        ),
                        "url": (
                            "https://"
                            "docs.python.org/3/"
                        ),
                        "content": (
                            "Official Python docs."
                        ),
                    },
                ]
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "documentation"
    )

    assert len(results) == 1

    assert (
        results[0].domain
        == "docs.python.org"
    )


def test_search_provider_timeout_is_safe_error(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        True,
    )

    def timeout_get(
        *args,
        **kwargs,
    ):
        raise httpx.TimeoutException(
            "Simulated timeout."
        )

    monkeypatch.setattr(
        httpx,
        "get",
        timeout_get,
    )

    retriever = WebRetriever()

    with pytest.raises(
        WebRetrievalProviderError
    ):
        retriever.search(
            "machine learning"
        )


def test_search_invalid_json_is_safe_error(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "app.rag.web.web_retriever."
            "settings.A4A_WEB_SEARCH_ENABLED"
        ),
        True,
    )

    class InvalidJsonResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError(
                "Invalid JSON."
            )

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: (
            InvalidJsonResponse()
        ),
    )

    retriever = WebRetriever()

    with pytest.raises(
        WebRetrievalProviderError
    ):
        retriever.search(
            "machine learning"
        )


def test_python_search_query_is_enriched():
    query = WebRetriever._build_search_query(
        "What is Python?"
    )

    assert query == (
        "What is Python? "
        "Python programming documentation"
    )


def test_python_search_query_enrichment_is_case_insensitive():
    query = WebRetriever._build_search_query(
        "Explain PyThOn dictionaries"
    )

    assert query == (
        "Explain PyThOn dictionaries "
        "Python programming documentation"
    )


def test_non_python_query_is_not_enriched():
    query = WebRetriever._build_search_query(
        "Explain machine learning"
    )

    assert query == (
        "Explain machine learning"
    )


def test_pythonic_substring_is_not_enriched():
    query = WebRetriever._build_search_query(
        "What does pythonic mean?"
    )

    assert query == (
        "What does pythonic mean?"
    )


def test_monty_python_query_is_not_enriched():
    query = WebRetriever._build_search_query(
        "Tell me about Monty Python"
    )

    assert query == (
        "Tell me about Monty Python"
    )


def test_python_query_uses_official_docs_when_search_has_no_results(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain Python generators"
    )

    assert len(results) == 1

    assert (
        results[0].domain
        == "docs.python.org"
    )

    assert (
        str(results[0].url)
        == "https://docs.python.org/3/"
    )


def test_python_official_docs_fallback_is_case_insensitive(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain PyThOn generators"
    )

    assert len(results) == 1

    assert (
        results[0].domain
        == "docs.python.org"
    )


def test_python_official_docs_fallback_not_used_for_non_python_query(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain machine learning"
    )

    assert results == []


def test_python_official_docs_fallback_not_used_for_monty_python(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Tell me about Monty Python"
    )

    assert results == []


def test_python_official_docs_candidate_still_requires_source_policy(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "pytorch.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain Python dictionaries"
    )

    assert results == []


def test_search_results_take_precedence_over_python_docs_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [
                    {
                        "title": (
                            "Python Tutorial"
                        ),
                        "url": (
                            "https://"
                            "docs.python.org/"
                            "3/tutorial/"
                        ),
                        "content": (
                            "Official Python "
                            "tutorial."
                        ),
                    }
                ]
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain Python dictionaries"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/"
        )
    )


# ---------------------------------------------------------
# Sprint 5.5.2.4K
# Deterministic official Python documentation routing
# ---------------------------------------------------------


def test_python_dictionary_query_routes_to_data_structures_docs(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain Python dictionaries"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/datastructures.html"
        )
    )


def test_python_dict_query_routes_to_data_structures_docs(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "How does a Python dict work?"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/datastructures.html"
        )
    )


def test_python_loop_query_routes_to_control_flow_docs(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Give me a Python loop example"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/controlflow.html"
        )
    )


def test_python_while_query_routes_to_control_flow_docs(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "Explain Python while loop"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/controlflow.html"
        )
    )


def test_python_arithmetic_query_routes_to_tutorial_intro(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "python syntax for adding 3+5"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == (
            "https://docs.python.org/"
            "3/tutorial/introduction.html"
        )
    )


def test_generic_python_query_keeps_docs_root_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "results": [],
            }
        ),
    )

    policy = WebSourcePolicy(
        "docs.python.org"
    )

    retriever = WebRetriever(
        source_policy=policy
    )

    results = retriever.search(
        "What is Python?"
    )

    assert len(results) == 1

    assert (
        str(results[0].url)
        == "https://docs.python.org/3/"
    )