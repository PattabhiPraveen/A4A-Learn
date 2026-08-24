from app.rag.chunking.chunker import (
    TextChunk,
    chunk_text,
)
from app.rag.chunking.deduplicator import (
    deduplicate_chunks,
)
from app.rag.chunking.text_cleaner import (
    clean_text,
)
from app.rag.ingestion.models import Document


def process_document(
    document: Document,
) -> list[TextChunk]:

    cleaned_text = clean_text(
        document.content
    )

    if not cleaned_text:
        return []

    chunks = chunk_text(
        text=cleaned_text,
        document_id=document.document_id,
        base_metadata={
            "source": document.source,
            "title": document.title,
            **document.metadata,
        },
    )

    return deduplicate_chunks(chunks)