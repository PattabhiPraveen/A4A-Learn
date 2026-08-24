from dataclasses import dataclass

from app.rag.chunking.metadata import (
    build_chunk_metadata,
)


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict


def chunk_text(
    text: str,
    document_id: str,
    base_metadata: dict | None = None,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[TextChunk]:

    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    metadata = base_metadata or {}

    chunks = []

    start = 0
    chunk_number = 0

    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:

            chunk_metadata = build_chunk_metadata(
                source=metadata.get("source", ""),
                title=metadata.get("title", ""),
                document_id=document_id,
                chunk_number=chunk_number,
                text=chunk,
                extension=metadata.get("extension"),
            )

            chunks.append(
                TextChunk(
                    chunk_id=f"{document_id}_{chunk_number}",
                    document_id=document_id,
                    text=chunk,
                    metadata=chunk_metadata,
                )
            )

        if end >= text_length:
            break

        start = end - overlap
        chunk_number += 1

    return chunks