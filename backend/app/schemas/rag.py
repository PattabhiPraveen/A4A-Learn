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