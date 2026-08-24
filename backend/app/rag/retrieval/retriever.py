from app.rag.embeddings.service import embed_query
from app.rag.retrieval.chroma_store import ChromaStore


class Retriever:

    def __init__(
        self,
        top_k: int = 3,
    ):

        self.top_k = top_k
        self.store = ChromaStore()

    def retrieve(
        self,
        query: str,
    ) -> list[dict]:

        if not query.strip():
            return []

        query_embedding = embed_query(
            query
        )

        results = (
            self.store.collection.query(
                query_embeddings=[
                    query_embedding
                ],
                n_results=self.top_k,
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )
        )

        documents = (
            results.get("documents", [[]])[0]
        )

        metadatas = (
            results.get("metadatas", [[]])[0]
        )

        distances = (
            results.get("distances", [[]])[0]
        )

        retrieved = []

        for index, document in enumerate(
            documents
        ):

            retrieved.append(
                {
                    "text": document,
                    "metadata": metadatas[index],
                    "distance": distances[index],
                }
            )

        return retrieved