"""
Governed documentation candidates for A4A Learn.

This registry controls discovery only.

All candidates must still pass WebSourcePolicy,
secure fetching, evidence selection, and grounding.
"""

import re

from app.rag.web.models import WebSearchResult


def select_documentation_candidate(
    question: str,
) -> WebSearchResult | None:
    """
    Return a fixed official-documentation candidate
    for a recognized technical-learning topic.

    Learner input never constructs a URL.
    """

    normalized = question.strip().lower()

    if not normalized:
        return None

    terms = set(
        re.findall(r"[a-z0-9_]+", normalized)
    )

    if "pandas" in terms:
        return WebSearchResult(
            title="Pandas User Guide",
            url="https://pandas.pydata.org/docs/user_guide/index.html",
            snippet="Official Pandas documentation and user guide.",
        )

    if "fastapi" in terms:
        return WebSearchResult(
            title="FastAPI Tutorial",
            url="https://fastapi.tiangolo.com/tutorial/",
            snippet="Official FastAPI tutorial and API development documentation.",
        )

    if (
        "args" in terms
        or "kwargs" in terms
        or "*args" in normalized
        or "**kwargs" in normalized
    ):
        return WebSearchResult(
            title="Python Function Definitions",
            url="https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
            snippet="Official Python tutorial covering function arguments.",
        )

    return None
