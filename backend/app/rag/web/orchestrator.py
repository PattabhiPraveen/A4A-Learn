import re

from app.rag.generation.ollama_client import OllamaClient
from app.rag.web.context_builder import build_web_context
from app.rag.web.evidence_fetcher import (
    WebEvidenceFetchError,
    WebEvidenceFetcher,
)
from app.rag.web.evidence_selector import EvidenceSelector
from app.rag.web.prompt_builder import (
    WEB_FALLBACK_MESSAGE,
    build_web_grounded_prompt,
)
from app.rag.web.web_retriever import (
    WebRetrievalDisabledError,
    WebRetriever,
)


_EXTERNAL_SOURCE_CITATION_PATTERN = re.compile(
    r"\[External Source\s+(\d+)\]",
    re.IGNORECASE,
)


class WebEvidenceOrchestrator:
    """
    Governed external-evidence fallback pipeline.

    Responsibilities:

    1. Discover approved external sources.
    2. Safely fetch sanitized page content.
    3. Select query-relevant bounded evidence.
    4. Build an untrusted-evidence context.
    5. Generate an answer using the local LLM.
    6. Require substantive answer content.
    7. Require valid external-source citations.
    8. Return explicit web provenance.

    External evidence is supplementary and is not treated
    as A4A Learn curriculum.

    Any failure to establish sufficient, substantive,
    cited evidence results in the governed fallback
    response.
    """

    def __init__(
        self,
        retriever=None,
        fetcher=None,
        llm=None,
        selector=None,
    ):
        self.retriever = (
            retriever
            or WebRetriever()
        )

        self.fetcher = (
            fetcher
            or WebEvidenceFetcher()
        )

        self.llm = (
            llm
            or OllamaClient()
        )

        self.selector = (
            selector
            or EvidenceSelector()
        )

    @staticmethod
    def _fallback_result(
        question: str,
    ) -> dict:
        """
        Return the canonical safe external-evidence
        fallback response.
        """

        return {
            "question": question,
            "answer": WEB_FALLBACK_MESSAGE,
            "grounded": False,
            "sources": [],
        }

    @staticmethod
    def _extract_citation_numbers(
        answer: str,
    ) -> set[int]:
        """
        Extract External Source citation numbers from a
        generated answer.

        Example:

        [External Source 1]
        [External Source 2]

        becomes:

        {1, 2}
        """

        matches = (
            _EXTERNAL_SOURCE_CITATION_PATTERN
            .findall(
                answer
            )
        )

        return {
            int(value)
            for value in matches
        }

    @classmethod
    def _has_valid_citations(
        cls,
        answer: str,
        evidence_count: int,
    ) -> bool:
        """
        Validate that a supported web answer contains at
        least one citation and that every cited source
        number exists in the supplied evidence context.

        This is intentionally fail-closed.

        It does not attempt semantic citation verification;
        it validates the citation contract and source
        numbering.
        """

        if evidence_count <= 0:
            return False

        citation_numbers = (
            cls._extract_citation_numbers(
                answer
            )
        )

        if not citation_numbers:
            return False

        return all(
            1 <= number <= evidence_count
            for number in citation_numbers
        )

    @classmethod
    def _has_substantive_answer(
        cls,
        answer: str,
    ) -> bool:
        """
        Return True only when meaningful answer content
        remains after external-source citations are
        removed.

        This is a structural grounding guard.

        It prevents output such as:

            [External Source 1]

        or:

            [External Source 1].

        from being accepted as a grounded learner answer.

        A short factual answer such as:

            8 [External Source 1]

        remains structurally valid.

        This method does not perform semantic entailment
        verification.
        """

        without_citations = (
            _EXTERNAL_SOURCE_CITATION_PATTERN.sub(
                "",
                answer,
            )
        )

        return bool(
            re.search(
                r"[A-Za-z0-9]",
                without_citations,
            )
        )

    def answer(
        self,
        question: str,
    ) -> dict:
        """
        Attempt to answer a question using approved
        supplementary external evidence.

        The caller controls whether web fallback is enabled.

        Provider, fetch, selection, generation, substantive
        answer, or citation insufficiency fails closed to
        WEB_FALLBACK_MESSAGE.

        WebRetrievalDisabledError is deliberately preserved
        so the production RAG service can distinguish an
        administratively disabled web path.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # -----------------------------------------
        # 1. Discover approved external candidates
        # -----------------------------------------

        try:
            candidates = (
                self.retriever.search(
                    question
                )
            )

        except WebRetrievalDisabledError:
            raise

        except Exception:
            return self._fallback_result(
                question
            )

        if not candidates:
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 2. Fetch and select bounded evidence
        # -----------------------------------------

        evidence = []

        for candidate in candidates:
            try:
                document = (
                    self.fetcher.fetch(
                        candidate
                    )
                )

                selected = (
                    self.selector.select(
                        question=question,
                        document=document,
                    )
                )

            except (
                WebEvidenceFetchError,
                ValueError,
            ):
                # One unusable external source must not
                # make the entire fallback pipeline
                # unavailable.
                continue

            evidence.append(
                selected
            )

        if not evidence:
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 3. Build bounded untrusted web context
        # -----------------------------------------

        context = build_web_context(
            evidence
        )

        if not context:
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 4. Build governed web-grounded prompt
        # -----------------------------------------

        prompt = build_web_grounded_prompt(
            question=question,
            context=context,
        )

        # -----------------------------------------
        # 5. Generate answer using local LLM
        # -----------------------------------------

        try:
            answer = self.llm.generate(
                prompt
            ).strip()

        except Exception:
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 6. Generation-level fallback guard
        # -----------------------------------------
        #
        # The fallback phrase must never coexist with
        # a supposedly supported answer.
        #
        # Checking containment rather than equality
        # also rejects mixed responses such as:
        #
        # "Python ... [External Source 1].
        #  I do not have enough information..."
        # -----------------------------------------

        if (
            not answer
            or WEB_FALLBACK_MESSAGE in answer
        ):
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 7. Substantive-answer guard
        # -----------------------------------------
        #
        # A citation by itself is not an answer.
        #
        # Remove all recognized external citations and
        # require at least one alphanumeric character
        # to remain.
        #
        # This is structural validation only and does
        # not claim semantic entailment.
        # -----------------------------------------

        if not self._has_substantive_answer(
            answer
        ):
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 8. Citation-contract validation
        # -----------------------------------------
        #
        # Every grounded web answer must contain at
        # least one valid citation, and every citation
        # number must correspond to evidence actually
        # supplied to the model.
        # -----------------------------------------

        if not self._has_valid_citations(
            answer=answer,
            evidence_count=len(
                evidence
            ),
        ):
            return self._fallback_result(
                question
            )

        # -----------------------------------------
        # 9. Build explicit web provenance
        # -----------------------------------------

        sources = []

        for item in evidence:
            sources.append(
                {
                    "title": item.title,
                    "source": str(
                        item.url
                    ),
                    "distance": None,
                    "source_type": "web",
                }
            )

        # -----------------------------------------
        # 10. Return grounded web answer
        # -----------------------------------------

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": sources,
        }