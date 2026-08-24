from dataclasses import dataclass, field


@dataclass
class Document:
    document_id: str
    source: str
    title: str
    content: str
    metadata: dict = field(default_factory=dict)