from enum import Enum


class TutorIntent(str, Enum):
    """
    Supported teaching intents for the A4A Learn AI Tutor.

    Intent controls how the Tutor should present a grounded answer.
    It must never be used to bypass retrieval, evidence validation,
    safety controls, or human-in-the-loop policies.
    """

    EXPLAIN = "explain"
    EXAMPLE = "example"
    SIMPLIFY = "simplify"
    PRACTICE = "practice"
    QUIZ = "quiz"
    DEBUG = "debug"
    COMPARE = "compare"
    SUMMARIZE = "summarize"
    LEARNING_GUIDANCE = "learning_guidance"
    GENERAL_QA = "general_qa"