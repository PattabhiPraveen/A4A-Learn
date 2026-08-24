from pathlib import Path

import chromadb

from app.rag.chunking.chunker import TextChunk
from app.rag.embeddings.service import embed_texts


PROJECT_ROOT = Path(__file__).resolve().parents[3]

CHROMA_PATH = (
    PROJECT_ROOT
    / "models"
    / "chroma"
)


COLLECTION_NAME = "a4a_education"


class ChromaStore:

    def __init__(self):

        CHROMA_PATH.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={
                    "description": (
                        "A4A Learn educational "
                        "knowledge base"
                    )
                },
            )
        )

    def add_chunks(
        self,
        chunks: list[TextChunk],
    ):

        if not chunks:
            return 0

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = embed_texts(
            texts
        )

        self.collection.upsert(
            ids=[
                chunk.chunk_id
                for chunk in chunks
            ],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                chunk.metadata
                for chunk in chunks
            ],
        )

        return len(chunks)

    def count(self) -> int:
        return self.collection.count()