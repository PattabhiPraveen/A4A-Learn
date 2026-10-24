import pytest

from app.core.config import settings
from app.rag.web.source_policy import WebSourcePolicy
from app.rag.web.web_retriever import (
    WebRetriever,
    WebRetrievalDisabledError,
    WebRetrievalProviderError,
)


def simulate_outage(*args, **kwargs):
    raise WebRetrievalProviderError(
        "Simulated SearXNG outage"
    )


def test_python_question_uses_approved_fallback(monkeypatch):
    monkeypatch.setattr(
        settings, "A4A_WEB_SEARCH_ENABLED", True
    )
    monkeypatch.setattr(
        WebRetriever, "_search_searxng", simulate_outage
    )

    retriever = WebRetriever(
        source_policy=WebSourcePolicy("docs.python.org")
    )

    results = retriever.search(
        "What is a Python dictionary?"
    )

    assert results
    assert all(
        str(result.url).startswith("https://docs.python.org/")
        for result in results
    )


def test_non_python_question_preserves_provider_error(monkeypatch):
    monkeypatch.setattr(
        settings, "A4A_WEB_SEARCH_ENABLED", True
    )
    monkeypatch.setattr(
        WebRetriever, "_search_searxng", simulate_outage
    )

    with pytest.raises(WebRetrievalProviderError):
        WebRetriever().search(
            "What is the weather in London?"
        )


def test_disabled_web_retrieval_never_calls_provider(monkeypatch):
    monkeypatch.setattr(
        settings, "A4A_WEB_SEARCH_ENABLED", False
    )

    def unexpected_call(*args, **kwargs):
        pytest.fail("Search provider must not be called")

    monkeypatch.setattr(
        WebRetriever, "_search_searxng", unexpected_call
    )

    with pytest.raises(WebRetrievalDisabledError):
        WebRetriever().search(
            "What is a Python dictionary?"
        )


def test_rejected_documentation_cannot_bypass_policy(monkeypatch):
    monkeypatch.setattr(
        settings, "A4A_WEB_SEARCH_ENABLED", True
    )
    monkeypatch.setattr(
        WebRetriever, "_search_searxng", simulate_outage
    )

    retriever = WebRetriever(
        source_policy=WebSourcePolicy("example.com")
    )

    with pytest.raises(WebRetrievalProviderError):
        retriever.search(
            "What is a Python dictionary?"
        )
