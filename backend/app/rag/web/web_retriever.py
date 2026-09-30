import re

import httpx

from app.core.config import settings
from app.rag.python_intent import (
    is_python_programming_query,
)
from app.rag.web.models import (
    TrustedWebEvidence,
    WebSearchResult,
)
from app.rag.web.source_policy import (
    WebSourcePolicy,
)


class WebRetrievalDisabledError(RuntimeError):
    """
    Raised when governed web retrieval is disabled.
    """

    pass


class WebRetrievalProviderError(RuntimeError):
    """
    Raised when the configured web search provider
    cannot provide a valid response.
    """

    pass


class WebRetriever:
    """
    Governed external-search boundary for A4A Learn.

    SearXNG remains the primary discovery provider.

    For genuine Python-programming questions, a small
    application-controlled set of official Python
    documentation pages may be used as deterministic
    discovery fallbacks when SearXNG produces no
    policy-approved evidence.

    Every fallback candidate must still cross
    WebSourcePolicy before it can become trusted
    external evidence.
    """

    _PYTHON_DOCS_ROOT = WebSearchResult(
        title="Python documentation",
        url="https://docs.python.org/3/",
        snippet=(
            "Official Python documentation for "
            "Python 3."
        ),
    )

    _PYTHON_DATA_STRUCTURES_DOCS = WebSearchResult(
        title="Python Tutorial - Data Structures",
        url=(
            "https://docs.python.org/"
            "3/tutorial/datastructures.html"
        ),
        snippet=(
            "Official Python tutorial documentation "
            "for data structures including lists, "
            "tuples, sets, and dictionaries."
        ),
    )

    _PYTHON_CONTROL_FLOW_DOCS = WebSearchResult(
        title="Python Tutorial - Control Flow",
        url=(
            "https://docs.python.org/"
            "3/tutorial/controlflow.html"
        ),
        snippet=(
            "Official Python tutorial documentation "
            "for control flow including for loops, "
            "while loops, range, and functions."
        ),
    )

    _PYTHON_INTRODUCTION_DOCS = WebSearchResult(
        title="Python Tutorial - Introduction",
        url=(
            "https://docs.python.org/"
            "3/tutorial/introduction.html"
        ),
        snippet=(
            "Official Python tutorial introduction "
            "covering numbers, arithmetic, operators, "
            "expressions, strings, and basic syntax."
        ),
    )

    # Exact token matching prevents accidental substring
    # routing such as "dictionarylike" or "loophole".
    _PYTHON_DATA_STRUCTURE_TERMS = {
        "dict",
        "dictionary",
        "dictionaries",
    }

    _PYTHON_CONTROL_FLOW_TERMS = {
        "for",
        "loop",
        "loops",
        "while",
    }

    _PYTHON_ARITHMETIC_TERMS = {
        "add",
        "adding",
        "addition",
        "arithmetic",
        "calculate",
        "calculation",
        "expression",
        "expressions",
        "math",
        "operator",
        "operators",
        "syntax",
    }

    def __init__(
        self,
        source_policy: WebSourcePolicy | None = None,
    ):
        self.source_policy = (
            source_policy
            or WebSourcePolicy()
        )

    @property
    def enabled(self) -> bool:
        """
        Return whether governed web retrieval is enabled.
        """

        return settings.A4A_WEB_SEARCH_ENABLED

    def filter_results(
        self,
        results: list[WebSearchResult],
    ) -> list[TrustedWebEvidence]:
        """
        Convert untrusted search-provider results into
        policy-approved evidence.

        Results from domains outside the configured
        allowlist are discarded.
        """

        approved: list[
            TrustedWebEvidence
        ] = []

        for result in results:
            evidence = (
                self.source_policy.approve(
                    result
                )
            )

            if evidence is None:
                continue

            approved.append(
                evidence
            )

            if (
                len(approved)
                >= settings.A4A_WEB_MAX_RESULTS
            ):
                break

        return approved

    @staticmethod
    def _build_search_query(
        question: str,
    ) -> str:
        """
        Build the provider-facing discovery query.

        Python-programming questions receive a small
        documentation-oriented discovery hint so broad
        general-web results are less likely to crowd out
        approved technical sources.

        The learner's original question remains unchanged
        for evidence selection and grounded generation.
        """

        normalized_question = (
            question.strip()
        )

        if not normalized_question:
            raise ValueError(
                "Web search question cannot be empty."
            )

        if is_python_programming_query(
            normalized_question
        ):
            return (
                f"{normalized_question} "
                "Python programming documentation"
            )

        return normalized_question

    @staticmethod
    def _question_terms(
        question: str,
    ) -> set[str]:
        """
        Extract normalized alphanumeric/underscore tokens
        for deterministic Python documentation routing.
        """

        return set(
            re.findall(
                r"[a-z0-9_]+",
                question.lower(),
            )
        )

    @classmethod
    def _select_python_docs_candidate(
        cls,
        question: str,
    ) -> WebSearchResult:
        """
        Select an application-controlled official Python
        documentation page for a Python-programming query.

        Routing is deterministic and does not permit the
        LLM or learner input to construct an arbitrary URL.

        More specific topics are checked before the generic
        documentation root.
        """

        terms = cls._question_terms(
            question
        )

        if (
            terms
            & cls._PYTHON_DATA_STRUCTURE_TERMS
        ):
            return (
                cls._PYTHON_DATA_STRUCTURES_DOCS
            )

        if (
            terms
            & cls._PYTHON_CONTROL_FLOW_TERMS
        ):
            return (
                cls._PYTHON_CONTROL_FLOW_DOCS
            )

        if (
            terms
            & cls._PYTHON_ARITHMETIC_TERMS
        ):
            return (
                cls._PYTHON_INTRODUCTION_DOCS
            )

        return cls._PYTHON_DOCS_ROOT

    def _python_docs_fallback(
        self,
        question: str,
    ) -> list[TrustedWebEvidence]:
        """
        Return a controlled official Python
        documentation candidate for a genuine
        Python-programming question.

        Topic-aware routing is deterministic.

        The selected candidate is not trusted
        automatically. It must still pass the configured
        WebSourcePolicy.
        """

        if not is_python_programming_query(
            question
        ):
            return []

        candidate = (
            self._select_python_docs_candidate(
                question
            )
        )

        evidence = (
            self.source_policy.approve(
                candidate
            )
        )

        if evidence is None:
            return []

        return [evidence]

    def _search_searxng(
        self,
        question: str,
    ) -> list[WebSearchResult]:
        """
        Query the local SearXNG service.

        Results returned by this method are candidate
        sources only. They have not yet crossed the
        A4A Learn trusted-source boundary.
        """

        normalized_question = (
            question.strip()
        )

        if not normalized_question:
            raise ValueError(
                "Web search question cannot be empty."
            )

        base_url = (
            settings.A4A_SEARXNG_BASE_URL
            .rstrip("/")
        )

        search_url = (
            f"{base_url}/search"
        )

        search_query = (
            self._build_search_query(
                normalized_question
            )
        )

        params = {
            "q": search_query,
            "format": "json",
            "safesearch": 2,
        }

        try:
            response = httpx.get(
                search_url,
                params=params,
                timeout=(
                    settings
                    .A4A_WEB_TIMEOUT_SECONDS
                ),
            )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise WebRetrievalProviderError(
                "Web search provider timed out."
            ) from exc

        except httpx.HTTPError as exc:
            raise WebRetrievalProviderError(
                "Web search provider request failed."
            ) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise WebRetrievalProviderError(
                "Web search provider returned "
                "invalid JSON."
            ) from exc

        raw_results = payload.get(
            "results",
            [],
        )

        if not isinstance(
            raw_results,
            list,
        ):
            raise WebRetrievalProviderError(
                "Web search provider returned "
                "an invalid results structure."
            )

        normalized_results: list[
            WebSearchResult
        ] = []

        for item in raw_results:
            if not isinstance(
                item,
                dict,
            ):
                continue

            title = str(
                item.get(
                    "title",
                    "",
                )
            ).strip()

            url = str(
                item.get(
                    "url",
                    "",
                )
            ).strip()

            snippet = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if not title:
                continue

            if not url:
                continue

            if not snippet:
                continue

            try:
                result = WebSearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                )

            except ValueError:
                # Ignore malformed provider results.
                continue

            normalized_results.append(
                result
            )

        return normalized_results

    def search(
        self,
        question: str,
    ) -> list[TrustedWebEvidence]:
        """
        Search external sources and return only evidence
        approved by WebSourcePolicy.

        SearXNG remains the primary discovery path.

        For genuine Python-programming questions only,
        a deterministic official Python documentation
        candidate is used when SearXNG produces no
        policy-approved evidence.

        The feature flag is enforced before any web
        retrieval path is allowed.
        """

        if not self.enabled:
            raise WebRetrievalDisabledError(
                "Governed web retrieval is disabled."
            )

        normalized_question = (
            question.strip()
        )

        if not normalized_question:
            raise ValueError(
                "Web search question cannot be empty."
            )

        candidates = (
            self._search_searxng(
                normalized_question
            )
        )

        approved = self.filter_results(
            candidates
        )

        if approved:
            return approved

        return self._python_docs_fallback(
            normalized_question
        )