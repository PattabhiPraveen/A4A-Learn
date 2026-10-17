from app.ai.tutor.intent_classifier import TutorIntentClassifier
from app.ai.tutor.teaching_policy import TutorTeachingPolicy
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
from app.rag.lesson_context import (
    LessonContextResolver,
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
        -> Tutor intent classification
        -> Teaching presentation strategy
        -> Selected governed lesson, when supplied
        -> Local curriculum retrieval
        -> Relevance filtering
        -> Local grounded generation
        -> Governed web fallback, when enabled
        -> Safe abstention when evidence is insufficient

    Tutor intent and teaching strategy control only how supported
    educational information is presented.

    They never change the evidence boundary, retrieval rules,
    authorization, web-fallback eligibility, grounding controls,
    or human-in-the-loop behavior.

    An explicitly selected lesson receives retrieval priority.

    Selection of a lesson does NOT automatically permit arbitrary
    client-provided lesson content. The selected lesson is resolved
    exclusively through LessonContextResolver, which provides
    governed server-side curriculum evidence.

    The resolved lesson evidence must satisfy the same
    RAG_MAX_DISTANCE relevance threshold before it can be used
    for grounded generation.

    If the selected lesson cannot produce a grounded answer,
    the normal curriculum RAG path continues.

    External web retrieval supplements the curriculum only when
    the local curriculum paths cannot produce a grounded answer.
    """

    def __init__(
        self,
        retriever=None,
        llm=None,
        web_orchestrator=None,
        lesson_context_resolver=None,
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

        self.lesson_context_resolver = (
            lesson_context_resolver
            if lesson_context_resolver is not None
            else LessonContextResolver()
        )

    @staticmethod
    def _get_teaching_strategy(
        question: str,
    ):
        """
        Resolve presentation strategy from learner intent.

        Intent controls teaching style only. Retrieval,
        grounding, fallback, and HITL remain authoritative.
        """

        intent = TutorIntentClassifier.classify(
            question
        )

        return TutorTeachingPolicy.get_strategy(
            intent
        )

    @staticmethod
    def _fallback_result(
        question: str,
    ) -> dict:
        """
        Return the canonical safe abstention response.
        """

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

    def _try_selected_lesson(
        self,
        question: str,
        lesson_id: str | None,
    ) -> dict | None:
        """
        Try the explicitly selected governed lesson first.

        IMPORTANT GOVERNANCE RULE:

        lesson selection establishes evidence priority only.

        The lesson content itself is never accepted directly from
        the browser. The lesson identifier is resolved through the
        server-side LessonContextResolver.

        The resolver's returned retrieval result is then subjected
        to the same RAG_MAX_DISTANCE threshold used by the normal
        curriculum RAG path.

        This design intentionally avoids sending the same question
        through the general retriever before evaluating the selected
        governed lesson. This ensures that an explicitly selected
        lesson receives priority.

        If the selected lesson cannot produce a grounded answer,
        None is returned and the normal curriculum RAG path
        continues.

        Returning None means either:

        - no lesson was selected,
        - the selected lesson cannot be resolved,
        - the selected lesson evidence is outside the allowed
          relevance threshold, or
        - the selected lesson cannot produce a grounded answer.

        Invalid or unknown lesson identifiers intentionally
        propagate to the API boundary rather than being silently
        treated as general Tutor requests.

        The resolver is called even when lesson_id is None so that
        the resolver remains the authoritative boundary for lesson
        context resolution and the general RAG path remains
        behaviorally consistent.
        """

        lesson_context = (
            self.lesson_context_resolver.resolve(
                lesson_id
            )
        )

        if lesson_context is None:
            return None

        lesson_result = (
            lesson_context.as_retrieval_result()
        )

        if not lesson_result:
            return None

        lesson_metadata = lesson_result.get(
            "metadata",
            {},
        )

        # -------------------------------------------------
        # The LessonContextResolver is the trusted server-side
        # source for explicitly selected lesson evidence.
        #
        # No lesson text supplied by the client is accepted.
        # -------------------------------------------------

        selected_lesson_title = (
            lesson_metadata.get(
                "title"
            )
        )

        selected_lesson_source = (
            lesson_metadata.get(
                "source"
            )
        )

        # -------------------------------------------------
        # Apply the same relevance threshold used by the
        # normal curriculum RAG path.
        #
        # The resolver-produced retrieval result contains
        # the governed lesson distance.
        # -------------------------------------------------

        try:
            selected_distance = float(
                lesson_result["distance"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

        if (
            selected_distance
            > settings.RAG_MAX_DISTANCE
        ):
            return None

        # -------------------------------------------------
        # Build trusted context directly from the governed
        # selected-lesson result.
        #
        # This is intentionally done before the general
        # retriever is invoked.
        # -------------------------------------------------

        context = build_context(
            [lesson_result]
        )

        teaching_strategy = (
            self._get_teaching_strategy(
                question
            )
        )

        prompt = build_grounded_prompt(
            question=question,
            context=context,
            teaching_strategy=teaching_strategy,
        )

        answer = self.llm.generate(
            prompt
        ).strip()

        # -------------------------------------------------
        # Generation-level grounding guardrail.
        #
        # Retrieval alone does not prove that the model
        # successfully answered the question.
        # -------------------------------------------------

        if (
            not answer
            or answer == FALLBACK_MESSAGE
        ):
            return None

        metadata = lesson_result.get(
            "metadata",
            {},
        )

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": [
                {
                    "title": metadata.get(
                        "title",
                        selected_lesson_title
                        or "Unknown source",
                    ),
                    "source": metadata.get(
                        "source",
                        selected_lesson_source,
                    ),
                    "distance": round(
                        selected_distance,
                        4,
                    ),
                    "source_type": (
                        "curriculum"
                    ),
                }
            ],
        }

    def answer(
        self,
        question: str,
        lesson_id: str | None = None,
    ) -> dict:
        """
        Answer a learner question through the governed
        A4A Learn RAG pipeline.

        Processing order:

        1. Validate question.
        2. Attempt explicitly selected governed lesson.
        3. If selected lesson cannot answer, use normal
           curriculum retrieval.
        4. Apply local relevance threshold.
        5. Generate grounded curriculum answer.
        6. If local curriculum cannot answer, use governed
           web fallback when enabled.
        7. Otherwise return safe abstention.

        Teaching intent controls presentation only.
        Evidence remains authoritative.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # -----------------------------------------
        # 0. Try explicitly selected lesson first.
        #
        # The lesson resolver is authoritative for the
        # selected lesson. Its governed result is evaluated
        # before the normal retriever is invoked.
        #
        # Selected lesson = evidence priority,
        # NOT automatic grounding validity.
        # -----------------------------------------

        lesson_result = (
            self._try_selected_lesson(
                question=question,
                lesson_id=lesson_id,
            )
        )

        if lesson_result is not None:
            return lesson_result

        # -----------------------------------------
        # 1. Retrieve local curriculum chunks.
        #
        # This is reached when:
        #
        # - no lesson was selected,
        # - selected lesson could not be resolved,
        # - selected lesson was not sufficiently relevant,
        # - or selected lesson generation abstained.
        # -----------------------------------------

        results = self.retriever.retrieve(
            question
        )

        # -----------------------------------------
        # 2. Apply local relevance threshold.
        # -----------------------------------------

        relevant_results = [
            result
            for result in results
            if float(result["distance"])
            <= settings.RAG_MAX_DISTANCE
        ]

        # -----------------------------------------
        # 3. No sufficient curriculum evidence.
        # -----------------------------------------

        if not relevant_results:
            return self._try_web_fallback(
                question
            )

        # -----------------------------------------
        # 4. Build trusted curriculum context.
        # -----------------------------------------

        context = build_context(
            relevant_results
        )

        # -----------------------------------------
        # 5. Resolve governed teaching strategy.
        # -----------------------------------------

        teaching_strategy = (
            self._get_teaching_strategy(
                question
            )
        )

        # -----------------------------------------
        # 6. Build local grounded prompt.
        # -----------------------------------------

        prompt = build_grounded_prompt(
            question=question,
            context=context,
            teaching_strategy=teaching_strategy,
        )

        # -----------------------------------------
        # 7. Generate local answer.
        # -----------------------------------------

        answer = self.llm.generate(
            prompt
        ).strip()

        # -----------------------------------------
        # 8. Generation-level grounding guardrail.
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
        # 9. Build curriculum provenance.
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
        # 10. Return grounded curriculum answer.
        # -----------------------------------------

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": sources,
        }