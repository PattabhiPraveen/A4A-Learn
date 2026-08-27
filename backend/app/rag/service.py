from app.core.config import settings
from app.rag.generation.context_builder import build_context
from app.rag.generation.ollama_client import OllamaClient
from app.rag.generation.prompt_builder import build_grounded_prompt
from app.rag.retrieval.retriever import Retriever


FALLBACK_MESSAGE = (
    "I do not have enough information in the learning materials "
    "to answer that question."
)


class RAGService:
    """
    Orchestrates the A4A Learn MVP RAG pipeline:

    Question
        -> Retrieval
        -> Relevance filtering
        -> Context construction
        -> Grounded prompt
        -> Local LLM
        -> Answer + sources
    """

    def __init__(self):

        self.retriever = Retriever(
            top_k=settings.RAG_TOP_K
        )

        self.llm = OllamaClient()

    def answer(
        self,
        question: str,
    ) -> dict:

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # -----------------------------------------
        # 1. Retrieve relevant educational chunks
        # -----------------------------------------

        results = self.retriever.retrieve(
            question
        )

        # -----------------------------------------
        # 2. Apply MVP relevance threshold
        # -----------------------------------------

        relevant_results = [
            result
            for result in results
            if float(result["distance"])
            <= settings.RAG_MAX_DISTANCE
        ]

        # -----------------------------------------
        # 3. Retrieval-level grounding guardrail
        # -----------------------------------------

        if not relevant_results:

            return {
                "question": question,
                "answer": FALLBACK_MESSAGE,
                "grounded": False,
                "sources": [],
            }

        # -----------------------------------------
        # 4. Build trusted context
        # -----------------------------------------

        context = build_context(
            relevant_results
        )

        # -----------------------------------------
        # 5. Build grounded LLM prompt
        # -----------------------------------------

        prompt = build_grounded_prompt(
            question=question,
            context=context,
        )

        # -----------------------------------------
        # 6. Generate local answer
        # -----------------------------------------

        answer = self.llm.generate(
            prompt
        )

        # -----------------------------------------
        # 7. Build unique source list
        # -----------------------------------------

        sources = []
        seen_titles = set()

        for result in relevant_results:

            metadata = result.get(
                "metadata",
                {},
            )

            title = metadata.get(
                "title",
                "Unknown source",
            )

            if title in seen_titles:
                continue

            seen_titles.add(title)

            sources.append(
                {
                    "title": title,
                    "source": metadata.get(
                        "source"
                    ),
                    "distance": round(
                        float(result["distance"]),
                        4,
                    ),
                }
            )

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": sources,
        }