from app.rag.generation.models import (
    RAGResponse,
    RAGSource,
)
from app.rag.generation.ollama_client import OllamaClient
from app.rag.generation.prompt_builder import build_grounded_prompt
from app.rag.retrieval.retriever import Retriever


INSUFFICIENT_CONTEXT_MESSAGE = (
    "I do not have enough information in the learning material "
    "to answer that."
)


class RAGService:
    """
    Orchestrates the A4A Learn grounded RAG pipeline.

    Flow:
        question
          -> semantic retrieval
          -> relevance filtering
          -> grounded prompt
          -> local LLM
          -> answer + sources
    """

    def __init__(
        self,
        top_k: int = 3,
        max_distance: float = 0.85,
    ):
        self.top_k = top_k
        self.max_distance = max_distance

        self.retriever = Retriever(
            top_k=top_k
        )

        self.llm = OllamaClient()

    def ask(
        self,
        question: str,
    ) -> RAGResponse:

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # -------------------------------------------------
        # 1. Retrieve semantically relevant learning chunks
        # -------------------------------------------------

        retrieved = self.retriever.retrieve(
            question
        )

        # -------------------------------------------------
        # 2. Apply relevance threshold
        #
        # ChromaDB distance:
        # lower distance = more relevant
        # -------------------------------------------------

        relevant = [
            item
            for item in retrieved
            if item.get("distance") is not None
            and item["distance"] <= self.max_distance
        ]

        # -------------------------------------------------
        # 3. Fail safely when knowledge is insufficient
        # -------------------------------------------------

        if not relevant:
            return RAGResponse(
                question=question,
                answer=INSUFFICIENT_CONTEXT_MESSAGE,
                sources=[],
            )

        # -------------------------------------------------
        # 4. Build grounded learning context
        # -------------------------------------------------

        contexts = [
            item["text"]
            for item in relevant
            if item.get("text")
        ]

        # -------------------------------------------------
        # 5. Build controlled prompt
        # -------------------------------------------------

        prompt = build_grounded_prompt(
            question=question,
            contexts=contexts,
        )

        # -------------------------------------------------
        # 6. Generate locally using Ollama
        # -------------------------------------------------

        answer = self.llm.generate(
            prompt
        ).strip()

        if not answer:
            answer = INSUFFICIENT_CONTEXT_MESSAGE

        # -------------------------------------------------
        # 7. Preserve source evidence
        # -------------------------------------------------

        sources = []

        for item in relevant:

            metadata = (
                item.get("metadata")
                or {}
            )

            source = metadata.get(
                "source",
                "unknown"
            )

            sources.append(
                RAGSource(
                    source=str(source),
                    distance=float(
                        item["distance"]
                    ),
                )
            )

        return RAGResponse(
            question=question,
            answer=answer,
            sources=sources,
        )