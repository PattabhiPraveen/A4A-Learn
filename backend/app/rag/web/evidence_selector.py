import re

from app.rag.web.models import (
    FetchedWebDocument,
    TrustedWebEvidence,
)


class EvidenceSelector:
    """
    Deterministically select a bounded, query-relevant
    evidence window from a sanitized external document.

    No LLM is used for evidence selection.

    The output is TrustedWebEvidence and is therefore
    bounded to the downstream 5,000-character evidence
    limit before it can enter the AI context.
    """

    MAX_EVIDENCE_CHARS = 5000
    WINDOW_RADIUS = 2200

    _TOKEN_PATTERN = re.compile(
        r"[A-Za-z_][A-Za-z0-9_.]*"
    )

    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "do",
        "does",
        "for",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "the",
        "to",
        "what",
        "with",
    }

    @classmethod
    def _query_terms(
        cls,
        question: str,
    ) -> list[str]:
        """
        Extract useful lexical terms from the question.

        Qualified identifiers are preserved and also
        decomposed into components.

        Example:

        pathlib.Path.read_text

        becomes useful terms including:

        pathlib.path.read_text
        pathlib
        path
        read_text
        """

        raw_terms = cls._TOKEN_PATTERN.findall(
            question
        )

        terms: list[str] = []

        for raw_term in raw_terms:
            normalized = (
                raw_term
                .lower()
                .strip(".")
            )

            if not normalized:
                continue

            if normalized in cls._STOP_WORDS:
                continue

            if normalized not in terms:
                terms.append(
                    normalized
                )

            # Also expose components of qualified
            # identifiers.
            #
            # pathlib.Path.read_text
            # ->
            # pathlib
            # path
            # read_text
            for component in normalized.split("."):
                if not component:
                    continue

                if component in cls._STOP_WORDS:
                    continue

                if component not in terms:
                    terms.append(
                        component
                    )

        return terms

    @classmethod
    def _find_best_position(
        cls,
        text: str,
        terms: list[str],
    ) -> int | None:
        """
        Select a deterministic lexical anchor.

        Longer terms are checked first so that specific
        identifiers such as read_text are preferred over
        short generic terms such as path.
        """

        lower_text = text.lower()

        ranked_terms = sorted(
            terms,
            key=len,
            reverse=True,
        )

        for term in ranked_terms:
            position = lower_text.find(
                term
            )

            if position >= 0:
                return position

        return None

    @classmethod
    def _bounded_window(
        cls,
        text: str,
        anchor: int,
    ) -> str:
        """
        Create a bounded evidence window around the
        selected lexical anchor.
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

        # If the selected region reaches the end of the
        # document, shift left where possible so that the
        # available evidence budget remains useful.
        start = max(
            0,
            end - cls.MAX_EVIDENCE_CHARS,
        )

        selected = text[
            start:end
        ].strip()

        return selected

    @classmethod
    def select(
        cls,
        question: str,
        document: FetchedWebDocument,
    ) -> TrustedWebEvidence:
        """
        Convert a fetched sanitized document into
        query-relevant bounded evidence.

        The returned TrustedWebEvidence can safely move
        to the downstream web context builder.
        """

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        text = document.content.strip()

        if not text:
            raise ValueError(
                "Fetched document content cannot be empty."
            )

        terms = cls._query_terms(
            question
        )

        anchor = cls._find_best_position(
            text=text,
            terms=terms,
        )

        if anchor is None:
            # No lexical anchor was found.
            #
            # Preserve deterministic fail-safe behavior
            # by selecting only the bounded beginning of
            # the document.
            #
            # This does not automatically make an answer
            # grounded. The downstream generation and
            # citation controls still apply.
            selected = text[
                : cls.MAX_EVIDENCE_CHARS
            ].strip()

        else:
            selected = cls._bounded_window(
                text=text,
                anchor=anchor,
            )

        if not selected:
            raise ValueError(
                "No usable external evidence was selected."
            )

        return TrustedWebEvidence(
            title=document.title,
            url=document.url,
            domain=document.domain,
            content=selected,
        )