from app.rag.chunking.chunker import chunk_text
from app.rag.chunking.deduplicator import deduplicate_chunks


def test_chunking_generates_chunks():

    text = "Indian Sign Language " * 100

    chunks = chunk_text(
        text=text,
        document_id="test-document",
        chunk_size=200,
        overlap=30,
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.text
        assert chunk.metadata["content_hash"]


def test_duplicate_chunks_are_removed():

    chunks = chunk_text(
        text="A4A Learn accessibility content.",
        document_id="test-document",
        chunk_size=800,
        overlap=100,
    )

    duplicated = chunks + chunks

    result = deduplicate_chunks(
        duplicated
    )

    assert len(result) == len(chunks)