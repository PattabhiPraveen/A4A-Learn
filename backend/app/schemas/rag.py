import uuid
from typing import Literal

from pydantic import BaseModel, Field


class RAGQuestion(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
    )


class RAGSource(BaseModel):
    """
    Evidence provenance returned with a RAG answer.

    Curriculum evidence may carry a vector-retrieval
    distance.

    External web evidence does not have an equivalent
    vector distance, so distance is None.
    """

    title: str

    source: str | None = None

    distance: float | None = None

    source_type: Literal[
        "curriculum",
        "web",
    ] = "curriculum"


class RAGResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    sources: list[RAGSource]

    # Runtime HITL workflow state.
    #
    # These fields describe the governed workflow around
    # the RAG result. They do not modify the RAG evidence.
    workflow_decision: str = "continue"
    escalation_reason: str = "normal"
    requires_human_review: bool = False
    review_id: uuid.UUID | None = None