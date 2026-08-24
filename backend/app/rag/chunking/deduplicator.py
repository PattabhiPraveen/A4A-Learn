from app.rag.chunking.chunker import TextChunk


def deduplicate_chunks(
    chunks: list[TextChunk],
) -> list[TextChunk]:

    seen_hashes = set()
    unique_chunks = []

    for chunk in chunks:

        content_hash = chunk.metadata.get(
            "content_hash"
        )

        if not content_hash:
            unique_chunks.append(chunk)
            continue

        if content_hash in seen_hashes:
            continue

        seen_hashes.add(content_hash)

        unique_chunks.append(chunk)

    return unique_chunks