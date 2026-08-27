from functools import lru_cache
from pathlib import Path

from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[4]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "embeddings"
    / "all-MiniLM-L6-v2"
)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the local embedding model once and reuse it.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Local embedding model not found: {MODEL_PATH}"
        )

    return SentenceTransformer(
        str(MODEL_PATH),
        local_files_only=True,
    )


def embed_texts(
    texts: list[str],
) -> list[list[float]]:

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embeddings.tolist()


def embed_query(
    query: str,
) -> list[float]:

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    model = get_embedding_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embedding.tolist()