from pathlib import Path

from typing import Any, List

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency at runtime
    _SentenceTransformer = None


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

PROJECT_ROOT = Path(__file__).resolve().parents[4]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "embeddings"
    / "all-MiniLM-L6-v2"
)


class EmbeddingModel:

    def __init__(self):
        if _SentenceTransformer is None:  # pragma: no cover - dependency is optional at type-check time
            raise ImportError(
                "sentence_transformers is required. Install with `pip install -U sentence-transformers`"
            )

        self.model = _SentenceTransformer(
            str(MODEL_PATH),
            local_files_only=True,
        )

    def encode(
        self,
        texts: List[str],
    ):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()