import hashlib


def generate_content_hash(text: str) -> str:
    """
    Generate a deterministic SHA-256 hash for content.
    Used for duplicate detection.
    """

    normalized = text.strip().lower()

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def build_chunk_metadata(
    source: str,
    title: str,
    document_id: str,
    chunk_number: int,
    text: str,
    extension: str | None = None,
) -> dict:

    metadata = {
        "source": source,
        "title": title,
        "document_id": document_id,
        "chunk_number": chunk_number,
        "content_hash": generate_content_hash(text),
    }

    if extension:
        metadata["extension"] = extension

    return metadata