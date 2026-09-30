from app.core.config import settings
from app.rag.generation.context_builder import (
    build_context,
)
from app.rag.generation.ollama_client import (
    OllamaClient,
)
from app.rag.generation.prompt_builder import (
    build_grounded_prompt,
)
from app.rag.retrieval.retriever import (
    Retriever,
)
from app.rag.web.orchestrator import (
    WebEvidenceOrchestrator,
)
from app.rag.web.web_retriever import (
    WebRetrievalDisabledError,
)


FALLBACK_MESSAGE = (
    "I do not have enough information in the learning materials "
    "to answer that question."
)


class RAGService:
    """
    Orchestrates the A4A Learn governed RAG pipeline.

    Processing order:

    Question
        -> Local curriculum retrieval
        -> Relevance filtering
        -> Local grounded generation
        -> Governed web fallback, when enabled
        -> Safe abstention when evidence is insufficient

    External web retrieval supplements the curriculum only when
    the local curriculum path cannot produce a grounded answer.
    """

    def __init__(
        self,
        retriever=None,
        llm=None,
        web_orchestrator=None,
    ):
        self.retriever = (
            retriever
            if retriever is not None
            else Retriever(
                top_k=settings.RAG_TOP_K
            )
        )

        self.llm = (
            llm
            if llm is not None
            else OllamaClient()
        )

        self.web_orchestrator = (
            web_orchestrator
            if web_orchestrator is not None
            else WebEvidenceOrchestrator(
                llm=self.llm
            )
        )

    @staticmethod
    def _fallback_result(
        question: str,
    ) -> dict:
        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "grounded": False,
            "sources": [],
        }

    def _try_web_fallback(
        self,
        question: str,
    ) -> dict:
        """
        Try supplementary governed web evidence only when the
        feature is enabled.

        Web provider/fetch/evidence insufficiency is represented
        by the web orchestrator as an ungrounded result.

        The production RAG contract intentionally converts any
        unsuccessful web attempt back to the canonical curriculum
        fallback so existing HITL behavior remains stable.
        """

        if not settings.A4A_WEB_SEARCH_ENABLED:
            return self._fallback_result(
                question
            )

        try:
            web_result = (
                self.web_orchestrator.answer(
                    question
                )
            )
        except WebRetrievalDisabledError:
            return self._fallback_result(
                question
            )

        if (
            web_result.get("grounded")
            and web_result.get("sources")
        ):
            return web_result

        return self._fallback_result(
            question
        )

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
        # 1. Retrieve local curriculum chunks
        # -----------------------------------------

        results = self.retriever.retrieve(
            question
        )

        # -----------------------------------------
        # 2. Apply local relevance threshold
        # -----------------------------------------

        relevant_results = [
            result
            for result in results
            if float(result["distance"])
            <= settings.RAG_MAX_DISTANCE
        ]

        # -----------------------------------------
        # 3. No sufficient curriculum evidence
        # -----------------------------------------

        if not relevant_results:
            return self._try_web_fallback(
                question
            )

        # -----------------------------------------
        # 4. Build trusted curriculum context
        # -----------------------------------------

        context = build_context(
            relevant_results
        )

        # -----------------------------------------
        # 5. Build local grounded prompt
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
        ).strip()

        # -----------------------------------------
        # 7. Generation-level grounding guardrail
        # -----------------------------------------
        #
        # Retrieval alone does not prove that the
        # model found enough evidence to answer.
        #
        # If the grounded local prompt causes the
        # model to abstain, the curriculum path is
        # insufficient and governed web fallback
        # may be attempted.
        # -----------------------------------------

        if (
            not answer
            or answer == FALLBACK_MESSAGE
        ):
            return self._try_web_fallback(
                question
            )

        # -----------------------------------------
        # 8. Build curriculum provenance
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
                        float(
                            result["distance"]
                        ),
                        4,
                    ),
                    "source_type": (
                        "curriculum"
                    ),
                }
            )

        # -----------------------------------------
        # 9. Return grounded curriculum answer
        # -----------------------------------------

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": sources,
        }