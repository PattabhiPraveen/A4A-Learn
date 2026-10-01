import re

from app.ai.tutor.intent import TutorIntent


class TutorIntentClassifier:
    """
    Lightweight deterministic intent classifier.

    This classifier identifies how a learner wants the Tutor to teach.
    It does not determine factual correctness, evidence sufficiency,
    authorization, web-fallback eligibility, or HITL escalation.
    """

    _PATTERNS: tuple[tuple[TutorIntent, tuple[str, ...]], ...] = (
        (
            TutorIntent.QUIZ,
            (
                r"\bquiz\s+me\b",
                r"\btest\s+me\b",
                r"\bask\s+me\s+(?:a\s+)?question",
                r"\bgive\s+me\s+(?:a\s+)?quiz\b",
            ),
        ),
        (
            TutorIntent.PRACTICE,
            (
                r"\bpractice\b",
                r"\bexercise\b",
                r"\bexercises\b",
                r"\bpractice\s+question",
                r"\bpractice\s+questions",
            ),
        ),
        (
            TutorIntent.DEBUG,
            (
                r"\bdebug\b",
                r"\bfix\s+(?:this|my)\s+code\b",
                r"\bwhat(?:'s|\s+is)\s+wrong\s+with\s+(?:this|my)\s+code\b",
                r"\bwhy\s+(?:does|is)\s+(?:this|my)\s+code\b",
                r"\berror\s+in\s+(?:this|my)\s+code\b",
            ),
        ),
        (
            TutorIntent.COMPARE,
            (
                r"\bcompare\b",
                r"\bdifference\s+between\b",
                r"\bwhat\s+is\s+the\s+difference\b",
                r"\bversus\b",
                r"\bvs\.?\b",
            ),
        ),
        (
            TutorIntent.SUMMARIZE,
            (
                r"\bsummarize\b",
                r"\bsummarise\b",
                r"\bsummary\b",
                r"\bkey\s+points\b",
                r"\bmain\s+points\b",
            ),
        ),
        (
            TutorIntent.SIMPLIFY,
            (
                r"\bsimplify\b",
                r"\bsimple\s+terms\b",
                r"\bsimpler\s+terms\b",
                r"\beasy\s+words\b",
                r"\beasier\s+way\b",
                r"\bexplain\s+simply\b",
                r"\bexplain\s+like\s+i(?:'m|\s+am)\s+a\s+beginner\b",
            ),
        ),
        (
            TutorIntent.EXAMPLE,
            (
                r"\bgive\s+me\s+(?:an?\s+)?example\b",
                r"\bshow\s+me\s+(?:an?\s+)?example\b",
                r"\bexample\s+of\b",
                r"\bwith\s+(?:an?\s+)?example\b",
                r"\bcode\s+example\b",
            ),
        ),
        (
            TutorIntent.EXPLAIN,
            (
                r"^\s*explain\b",
                r"\bexplain\s+(?:this|the|how|why|what)\b",
                r"\bhelp\s+me\s+understand\b",
                r"\bteach\s+me\b",
            ),
        ),
        (
            TutorIntent.LEARNING_GUIDANCE,
            (
                r"\bwhat\s+should\s+i\s+learn\b",
                r"\bwhat\s+should\s+i\s+study\b",
                r"\bwhat\s+should\s+i\s+learn\s+next\b",
                r"\bwhat\s+should\s+i\s+study\s+next\b",
                r"\bwhat\s+should\s+i\s+do\s+next\b",
                r"\bwhere\s+should\s+i\s+start\b",
                r"\blearning\s+path\b",
                r"\bstudy\s+plan\b",
            ),
        ),
    )

    @classmethod
    def classify(cls, question: str) -> TutorIntent:
        """
        Classify a learner question into one teaching intent.

        Empty or unmatched input safely falls back to GENERAL_QA.
        """

        if not isinstance(question, str):
            return TutorIntent.GENERAL_QA

        normalized = cls._normalize(question)

        if not normalized:
            return TutorIntent.GENERAL_QA

        for intent, patterns in cls._PATTERNS:
            for pattern in patterns:
                if re.search(pattern, normalized, flags=re.IGNORECASE):
                    return intent

        return TutorIntent.GENERAL_QA

    @staticmethod
    def _normalize(question: str) -> str:
        return " ".join(question.strip().split()).lower()