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

_WORD_PATTERN = re.compile(
    r"[A-Za-z0-9]+",
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "its",
    "may",
    "might",
    "more",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "under",
    "was",
    "were",
    "what",
    "when",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
}



from app.core.logging import logger


class WebEvidenceOrchestrator:
    """
    Governed external-evidence fallback pipeline.

    Responsibilities:

    1. Discover approved external sources.
    2. Safely fetch sanitized page content.
    3. Select query-relevant bounded evidence.
    4. Deduplicate equivalent external sources.
    5. Build an untrusted-evidence context.
    6. Generate an answer using the local LLM.
    7. Require a substantive answer.
    8. Require valid external-source citations.
    9. Validate citation-to-evidence semantic support.
    10. Return explicit web provenance.

    External evidence is supplementary and is not treated
    as A4A Learn curriculum.

    Any failure to establish sufficient, cited, supported
    evidence results in the governed fallback response.
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
        Extract External Source citation numbers.

        Example:

            [External Source 1]
            [External Source 2]

        becomes:

            {1, 2}
        """

        matches = (
            _EXTERNAL_SOURCE_CITATION_PATTERN.findall(
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
        Validate that a supported web answer contains
        at least one citation and that every cited source
        number exists in the supplied evidence context.

        This validates citation numbering only.
        Semantic support is validated separately.
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

    @staticmethod
    def _has_substantive_answer(
        answer: str | None,
    ) -> bool:
        """
        Determine whether the generated answer contains
        meaningful natural-language or factual content.

        Citation-only responses are not substantive.

        Examples rejected:

            [External Source 1]

            [External Source 1].

            [External Source 1]!

        Examples accepted:

            Python is a programming language.
            [External Source 1]

            8 [External Source 1]
        """

        if not answer:
            return False

        normalized = answer.strip()

        if not normalized:
            return False

        without_citations = (
            _EXTERNAL_SOURCE_CITATION_PATTERN.sub(
                "",
                normalized,
            )
        )

        without_links = re.sub(
            r"\[[^\]]+\]\([^)]+\)",
            "",
            without_citations,
        )

        meaningful = re.sub(
            r"[\s\W_]+",
            "",
            without_links,
            flags=re.UNICODE,
        )

        return bool(meaningful)

    @staticmethod
    def _normalize_evidence_terms(
        text: str,
    ) -> set[str]:
        """
        Convert text into deterministic meaningful terms.

        Stop words are removed.

        Numeric tokens are preserved because concise factual
        answers such as:

            8 [External Source 1]

        can be directly supported by evidence containing 8.
        """

        if not text:
            return set()

        words = _WORD_PATTERN.findall(
            text.lower()
        )

        # Normalize explicitly approved word forms.
        # Avoid broad stemming of technical terminology.
        word_forms = {
            "define": "define",
            "defined": "define",
            "defining": "define",
            "defines": "define",
        }

        return {
            word_forms.get(word, word)
            for word in words
            if word not in _STOP_WORDS and word != "also"
        }

    @classmethod
    def _extract_citation_claims(
        cls,
        answer: str,
    ) -> list[tuple[int, str]]:
        """
        Extract the answer claim associated with each
        external-source citation.

        A citation normally appears after the sentence it
        supports, for example:

            Python supports dictionaries [External Source 1].

        The sentence-ending punctuation belongs to the claim,
        not to the boundary preceding the claim.

        Therefore terminal punctuation immediately before the
        citation is removed before sentence-boundary detection.

        Earlier citations are removed from the claim window so
        multiple citations supporting the same statement do not
        become part of the lexical claim itself.

        Citation-only responses intentionally produce an empty
        claim and are rejected by semantic validation.
        """

        if not answer:
            return []

        claims = []

        for match in _EXTERNAL_SOURCE_CITATION_PATTERN.finditer(
            answer
        ):
            citation_number = int(
                match.group(1)
            )

            # -------------------------------------------------
            # Everything before this citation is the candidate
            # claim window.
            # -------------------------------------------------

            preceding = answer[
                :match.start()
            ].rstrip()

            # -------------------------------------------------
            # Remove any earlier citation markers from the
            # candidate claim. This prevents:
            #
            #   Claim [External Source 1] Claim2 [External Source 2]
            #
            # from treating Source 1 as part of Claim2.
            # -------------------------------------------------

            preceding = _EXTERNAL_SOURCE_CITATION_PATTERN.sub(
                "",
                preceding,
            ).rstrip()

            # -------------------------------------------------
            # IMPORTANT:
            #
            # If the model generated:
            #
            #   "... key:value pairs. [External Source 1]"
            #
            # match.start() is immediately after the period.
            #
            # Do NOT treat that terminal period as the sentence
            # boundary. It belongs to the current claim.
            #
            # Remove only terminal sentence punctuation before
            # looking for the PREVIOUS sentence boundary.
            # -------------------------------------------------

            preceding_for_boundary = re.sub(
                r"[.!?]+\s*$",
                "",
                preceding,
            ).rstrip()

            boundary_positions = [
                preceding_for_boundary.rfind("."),
                preceding_for_boundary.rfind("!"),
                preceding_for_boundary.rfind("?"),
                preceding_for_boundary.rfind("\n"),
            ]

            boundary = max(
                boundary_positions
            )

            claim = preceding_for_boundary[
                boundary + 1:
            ].strip()

            claims.append(
                (
                    citation_number,
                    claim,
                )
            )

        return claims


    @classmethod
    def _claim_has_numeric_support(
        cls,
        claim_terms: set[str],
        evidence_terms: set[str],
    ) -> bool:
        """
        Check direct numeric support.

        Example:

            8 [External Source 1]

        is accepted when the cited evidence contains 8.
        """

        claim_numbers = {
            term
            for term in claim_terms
            if term.isdigit()
        }

        if not claim_numbers:
            return False

        evidence_numbers = {
            term
            for term in evidence_terms
            if term.isdigit()
        }

        return claim_numbers.issubset(
            evidence_numbers
        )

    @classmethod
    def _claim_has_lexical_support(
        cls,
        claim: str,
        evidence: str,
    ) -> bool:
        """
        Determine whether a citation-supported claim has
        meaningful lexical support in the cited evidence.

        Source-reference/provenance statements are allowed
        because they do not introduce a new factual claim.

        Examples accepted:

            Python uses indentation to define code blocks.

            The same approved source provides the supporting
            evidence.

        Example rejected:

            Python was created in 1991.

        when the cited evidence does not support that claim.
        """

        claim_terms = cls._normalize_evidence_terms(
            claim
        )

        evidence_terms = cls._normalize_evidence_terms(
            evidence
        )

        if not claim_terms or not evidence_terms:
            return False

        # -------------------------------------------------
        # Source-reference / provenance language
        # -------------------------------------------------

        provenance_terms = {
            "source",
            "sources",
            "evidence",
            "reference",
            "references",
            "cited",
            "citation",
            "approved",
            "supporting",
            "supports",
            "supported",
            "according",
            "document",
            "documentation",
            "same",
            "provides",
            "provided",
            "above",
            "below",
            "previous",
            "following",
        }

        # A statement consisting entirely of provenance
        # language does not introduce a new factual claim.
        if claim_terms.issubset(
            provenance_terms
        ):
            return True

        # -------------------------------------------------
        # Numeric support
        # -------------------------------------------------

        # Numeric-only claims may use direct numeric support.
        # Mixed claims must also pass lexical validation.
        if all(term.isdigit() for term in claim_terms):
            return cls._claim_has_numeric_support(
                claim_terms=claim_terms,
                evidence_terms=evidence_terms,
            )

        # -------------------------------------------------
        # Meaningful lexical overlap
        # -------------------------------------------------

        # Reject unsupported numbers, even when other
        # claim terms overlap with the evidence.
        claim_numbers = {
            term for term in claim_terms
            if term.isdigit()
        }
        evidence_numbers = {
            term for term in evidence_terms
            if term.isdigit()
        }

        if not claim_numbers.issubset(evidence_numbers):
            return False

        # Conservative lexical coverage:
        # every normalized claim term must be evidenced.
        return claim_terms.issubset(evidence_terms)

    @classmethod
    def _has_semantic_citation_support(
        cls,
        answer: str,
        evidence,
    ) -> bool:
        """
        Validate that every citation in the generated
        answer has meaningful support in its cited evidence.

        This is a deterministic first-line guardrail.

        It does not claim full natural-language entailment.
        It establishes a conservative lexical support
        contract before an answer can be marked grounded.

        Fail-closed behavior:

        - no citations -> False
        - invalid citation number -> False
        - citation without a claim -> False
        - unsupported claim -> False
        - all cited claims supported -> True
        """

        if not answer:
            return False

        if not evidence:
            return False

        claims = cls._extract_citation_claims(
            answer
        )

        if not claims:
            return False

        evidence_by_number = {
            index: item
            for index, item in enumerate(
                evidence,
                start=1,
            )
        }

        for citation_number, claim in claims:
            item = evidence_by_number.get(
                citation_number
            )

            if item is None:
                return False

            if not claim:
                return False

            if not cls._claim_has_lexical_support(
                claim=claim,
                evidence=item.content,
            ):
                return False

        return True

    @staticmethod
    def _deduplicate_evidence(
        evidence,
    ):
        """
        Remove duplicate external evidence by URL or
        normalized evidence content.

        Rules:

        1. Same URL:
           Keep the first occurrence.

        2. Different URLs with identical normalized
           evidence content:
           Keep the first occurrence.

        3. Different URLs with different evidence:
           Keep both.

        First occurrence wins so source ordering and
        citation numbering remain deterministic.
        """

        seen_urls = set()
        seen_content = set()
        unique = []

        for item in evidence:
            url = str(
                item.url
            ).strip()

            content = (
                item.content
                or ""
            ).strip()

            if not url or not content:
                continue

            normalized_content = re.sub(
                r"\s+",
                " ",
                content,
            ).strip().lower()

            if url in seen_urls:
                continue

            if normalized_content in seen_content:
                continue

            seen_urls.add(
                url
            )

            seen_content.add(
                normalized_content
            )

            unique.append(
                item
            )

        return unique

    def answer(
        self,
        question: str,
    ) -> dict:
        """
        Attempt to answer a question using approved
        supplementary external evidence.

        Provider/fetch/selection/generation insufficiency
        fails closed to WEB_FALLBACK_MESSAGE.

        WebRetrievalDisabledError is deliberately preserved
        so the production RAG service can distinguish an
        administratively disabled web path.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        # -------------------------------------------------
        # 1. Discover approved external evidence candidates
        # -------------------------------------------------

        try:
            candidates = self.retriever.search(
                question
            )

        except WebRetrievalDisabledError:
            raise

        except Exception:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_SEARCH_ERROR")
            return self._fallback_result(
                question
            )

        if not candidates:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_NO_CANDIDATES")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 2. Fetch and select bounded relevant evidence
        # -------------------------------------------------

        evidence = []

        for candidate in candidates:
            try:
                fetched = self.fetcher.fetch(
                    candidate
                )

                selected = self.selector.select(
                    question=question,
                    document=fetched,
                )

                evidence.append(
                    selected
                )

            except (
                WebEvidenceFetchError,
                ValueError,
            ):
                # One bad external source must not fail
                # the entire fallback path.
                continue

        if not evidence:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_NO_EVIDENCE")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 3. Deduplicate approved evidence
        # -------------------------------------------------

        evidence = self._deduplicate_evidence(
            evidence
        )

        if not evidence:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_NO_EVIDENCE_AFTER_DEDUP")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 4. Build bounded untrusted external context
        # -------------------------------------------------

        context = build_web_context(
            evidence
        )

        if not context.strip():
            logger.info("a4a_web_rag_failure reason=%s", "WEB_EMPTY_CONTEXT")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 5. Build grounded external-evidence prompt
        # -------------------------------------------------

        prompt = build_web_grounded_prompt(
            question=question,
            context=context,
        )

        # -------------------------------------------------
        # 6. Generate using local Ollama
        # -------------------------------------------------

        try:
            answer = self.llm.generate(
                prompt
            ).strip()

        except Exception:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_GENERATION_ERROR")
            return self._fallback_result(
                question
            )

        if not answer:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_EMPTY_ANSWER")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 7. Reject governed fallback response
        # -------------------------------------------------

        if WEB_FALLBACK_MESSAGE in answer:
            logger.info("a4a_web_rag_failure reason=%s", "WEB_MODEL_ABSTENTION")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 8. Substantive-answer validation
        # -------------------------------------------------

        if not self._has_substantive_answer(
            answer
        ):
            logger.info("a4a_web_rag_failure reason=%s", "WEB_NON_SUBSTANTIVE_ANSWER")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 9. Citation contract validation
        # -------------------------------------------------

        # Retry once only when an otherwise substantive
        # answer has omitted all external citations.
        # Reuse the original approved evidence context.
        if not self._extract_citation_numbers(answer):
            retry_prompt = (
                prompt
                + "\n\nFINAL ANSWER REQUIREMENT:\n"
                + "Answer the learner's original question "
                + "using only the approved external evidence "
                + "provided above. Include valid citations "
                + "such as [External Source 1] immediately "
                + "after supported factual claims. "
                + "Use only source numbers present in the "
                + "approved evidence. Do not invent citations. "
                + "If evidence is insufficient, return the "
                + "required fallback message."
            )

            try:
                answer = self.llm.generate(
                    retry_prompt
                ).strip()
            except Exception:
                logger.info("a4a_web_rag_failure reason=%s", "WEB_CITATION_RETRY_ERROR")
                return self._fallback_result(
                    question
                )

            if (
                not answer
                or WEB_FALLBACK_MESSAGE in answer
                or not self._has_substantive_answer(answer)
            ):
                logger.info("a4a_web_rag_failure reason=%s", "WEB_CITATION_RETRY_REJECTED")
                return self._fallback_result(
                    question
                )

        if not self._has_valid_citations(
            answer=answer,
            evidence_count=len(evidence),
        ):
            logger.info("a4a_web_rag_failure reason=%s", "WEB_CITATION_INVALID")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 10. Citation-to-evidence semantic validation
        # -------------------------------------------------

        if not self._has_semantic_citation_support(
            answer=answer,
            evidence=evidence,
        ):
            logger.info("a4a_web_rag_failure reason=%s", "WEB_CLAIM_UNSUPPORTED")
            return self._fallback_result(
                question
            )

        # -------------------------------------------------
        # 11. Explicit external-source provenance
        # -------------------------------------------------

        sources = [
            {
                "title": item.title,
                "source": str(item.url),
                "distance": None,
                "source_type": "web",
            }
            for item in evidence
        ]

        return {
            "question": question,
            "answer": answer,
            "grounded": True,
            "sources": sources,
        }