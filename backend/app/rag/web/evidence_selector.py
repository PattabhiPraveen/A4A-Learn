import re

from app.rag.web.models import (
    FetchedWebDocument,
    TrustedWebEvidence,
)


class EvidenceSelector:
    """
    Select bounded, query-relevant evidence from a sanitized
    external web document.

    Security properties:

    - Never returns the complete external document.
    - Requires lexical relevance to the user question.
    - Selects a bounded evidence window.
    - Preserves source provenance.
    - Fails closed when no relevant evidence is found.
    """

    MAX_EVIDENCE_CHARS = 5000
    WINDOW_RADIUS = 2500

    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "tell",
        "the",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    _TERM_PATTERN = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9_.+-]*"
    )

    @classmethod
    def _query_terms(
        cls,
        question: str,
    ) -> list[str]:
        """
        Extract meaningful lexical terms from the
        user question.

        Punctuation is removed from the extracted
        terms so that:

            "Python."

        correctly matches:

            "Python"

        Stop words are removed so that generic words
        do not become relevance anchors.
        """

        terms = []

        for match in cls._TERM_PATTERN.finditer(
            question
        ):
            term = match.group(0).strip()

            if not term:
                continue

            # Normalize punctuation around the term.
            normalized = term.strip(
                ".,;:!?()[]{}\"'`"
            ).lower()

            if not normalized:
                continue

            if normalized in cls._STOP_WORDS:
                continue

            # Keep meaningful numeric tokens such as
            # "3" and "5" because they can be critical
            # to factual questions.
            if (
                len(normalized) < 2
                and not normalized.isdigit()
            ):
                continue

            terms.append(
                normalized
            )

        # Prefer specific/longer terms first.
        return sorted(
            set(terms),
            key=lambda value: (
                -len(value),
                value,
            ),
        )

    @classmethod
    def _find_anchor(
        cls,
        *,
        text: str,
        terms: list[str],
    ) -> int | None:
        """
        Find the earliest relevant lexical anchor in
        the document.

        Longer/more-specific terms are evaluated first.
        """

        if not text:
            return None

        lowered = text.lower()

        for term in terms:
            position = lowered.find(
                term
            )

            if position >= 0:
                return position

        return None

    @classmethod
    def _bounded_window(
        cls,
        *,
        text: str,
        anchor: int,
    ) -> str:
        """
        Return a bounded evidence window around the
        relevance anchor.
        """

        if len(text) <= cls.MAX_EVIDENCE_CHARS:
            return text.strip()

        start = max(
            0,
            anchor - cls.WINDOW_RADIUS,
        )

        end = min(
            len(text),
            start + cls.MAX_EVIDENCE_CHARS,
        )

        # If the anchor is close to the end of the
        # document, shift the window backward so that
        # the requested maximum size is preserved.
        if (
            end - start
            < cls.MAX_EVIDENCE_CHARS
        ):
            start = max(
                0,
                end - cls.MAX_EVIDENCE_CHARS,
            )

        return text[
            start:end
        ].strip()

    @classmethod
    def select(
        cls,
        *,
        question: str,
        document: FetchedWebDocument,
    ) -> TrustedWebEvidence:
        """
        Select bounded, query-relevant evidence.

        The selector fails closed when:

        - the question is empty;
        - the document content is empty;
        - no meaningful query terms exist;
        - no query term is found in the document.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        if document is None:
            raise ValueError(
                "Document cannot be empty."
            )

        text = (
            document.content
            or ""
        ).strip()

        if not text:
            raise ValueError(
                "Document content cannot be empty."
            )

        terms = cls._query_terms(
            question
        )

        if not terms:
            raise ValueError(
                "No meaningful query terms found."
            )

        anchor = cls._find_anchor(
            text=text,
            terms=terms,
        )

        # Fail closed when the retrieved document
        # does not contain query-relevant evidence.
        #
        # Do NOT fall back to the first 5,000
        # characters because that could inject
        # unrelated web content into the grounded
        # generation context.
        if anchor is None:
            raise ValueError(
                "No query-relevant external evidence "
                "was found."
            )

        selected = cls._bounded_window(
            text=text,
            anchor=anchor,
        )

        if not selected:
            raise ValueError(
                "Selected evidence is empty."
            )

        return TrustedWebEvidence(
            title=document.title,
            url=document.url,
            domain=document.domain,
            content=selected,
        )