import uuid

from pydantic import BaseModel, Field


class RAGQuestion(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
    )


class RAGSource(BaseModel):
    title: str
    source: str | None = None
    distance: float


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
