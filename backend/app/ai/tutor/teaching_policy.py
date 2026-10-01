from dataclasses import dataclass

from app.ai.tutor.intent import TutorIntent


@dataclass(frozen=True)
class TeachingStrategy:
    """
    Presentation strategy for a Tutor intent.

    A strategy controls how grounded educational information should
    be presented. It does not grant permission to use unsupported
    knowledge or bypass evidence, safety, authorization, or HITL.
    """

    intent: TutorIntent
    instruction: str
    preferred_structure: tuple[str, ...]


class TutorTeachingPolicy:
    """
    Maps learner intent to an accessible teaching strategy.

    All factual educational content must still come from the governed
    evidence pipeline.
    """

    _STRATEGIES: dict[TutorIntent, TeachingStrategy] = {
        TutorIntent.EXPLAIN: TeachingStrategy(
            intent=TutorIntent.EXPLAIN,
            instruction=(
                "Explain the concept clearly using only the provided "
                "learning evidence. Use concise learner-friendly language."
            ),
            preferred_structure=(
                "Concept",
                "Explanation",
                "Key takeaway",
            ),
        ),

        TutorIntent.EXAMPLE: TeachingStrategy(
            intent=TutorIntent.EXAMPLE,
            instruction=(
                "Teach through a simple example grounded in the provided "
                "learning evidence. Explain what the example demonstrates."
            ),
            preferred_structure=(
                "Concept",
                "Example",
                "Why it works",
            ),
        ),

        TutorIntent.SIMPLIFY: TeachingStrategy(
            intent=TutorIntent.SIMPLIFY,
            instruction=(
                "Explain the provided learning evidence using short, "
                "plain-language sentences. Avoid unnecessary jargon."
            ),
            preferred_structure=(
                "Simple explanation",
                "Example",
                "Remember",
            ),
        ),

        TutorIntent.PRACTICE: TeachingStrategy(
            intent=TutorIntent.PRACTICE,
            instruction=(
                "Create a short practice activity based only on the "
                "provided learning evidence. Do not introduce concepts "
                "that are absent from the evidence."
            ),
            preferred_structure=(
                "Practice task",
                "What to try",
                "Hint",
            ),
        ),

        TutorIntent.QUIZ: TeachingStrategy(
            intent=TutorIntent.QUIZ,
            instruction=(
                "Create a concise learning question based only on the "
                "provided evidence. Do not introduce unsupported facts."
            ),
            preferred_structure=(
                "Question",
                "Learner response",
                "Feedback",
            ),
        ),

        TutorIntent.DEBUG: TeachingStrategy(
            intent=TutorIntent.DEBUG,
            instruction=(
                "Help identify the programming problem using the provided "
                "learning evidence. Explain the issue and a grounded "
                "correction without inventing unavailable facts."
            ),
            preferred_structure=(
                "Issue",
                "Why it happens",
                "Correction",
            ),
        ),

        TutorIntent.COMPARE: TeachingStrategy(
            intent=TutorIntent.COMPARE,
            instruction=(
                "Compare the requested concepts using only information "
                "supported by the provided learning evidence."
            ),
            preferred_structure=(
                "Concept A",
                "Concept B",
                "Key differences",
            ),
        ),

        TutorIntent.SUMMARIZE: TeachingStrategy(
            intent=TutorIntent.SUMMARIZE,
            instruction=(
                "Summarize only the provided learning evidence. Preserve "
                "important terminology and do not add outside facts."
            ),
            preferred_structure=(
                "Summary",
                "Key points",
            ),
        ),

        TutorIntent.LEARNING_GUIDANCE: TeachingStrategy(
            intent=TutorIntent.LEARNING_GUIDANCE,
            instruction=(
                "Provide learning guidance using only available curriculum "
                "and learner-context evidence. Do not infer learner ability, "
                "disability, or progress that is not explicitly provided."
            ),
            preferred_structure=(
                "Current focus",
                "Recommended next step",
                "Reason",
            ),
        ),

        TutorIntent.GENERAL_QA: TeachingStrategy(
            intent=TutorIntent.GENERAL_QA,
            instruction=(
                "Answer the learner's question clearly using only the "
                "provided learning evidence."
            ),
            preferred_structure=(
                "Answer",
                "Key takeaway",
            ),
        ),
    }

    @classmethod
    def get_strategy(
        cls,
        intent: TutorIntent,
    ) -> TeachingStrategy:
        """
        Return the governed presentation strategy for an intent.

        Unknown values fail safely to GENERAL_QA.
        """

        if not isinstance(intent, TutorIntent):
            return cls._STRATEGIES[TutorIntent.GENERAL_QA]

        return cls._STRATEGIES.get(
            intent,
            cls._STRATEGIES[TutorIntent.GENERAL_QA],
        )