from dataclasses import dataclass, field


@dataclass
class RAGSource:
    source: str
    distance: float | None = None


@dataclass
class RAGResponse:
    question: str
    answer: str
    sources: list[RAGSource] = field(
        default_factory=list
    )