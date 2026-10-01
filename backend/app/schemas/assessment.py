from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


AssessmentRecommendation = Literal[
    "review",
    "practice",
    "continue",
]


class AssessmentQuestionResponse(BaseModel):
    """
    Learner-safe assessment question.

    The correct answer is intentionally excluded.
    """

    id: str = Field(
        min_length=1,
        max_length=50,
    )

    question: str = Field(
        min_length=1,
        max_length=1000,
    )

    options: list[str] = Field(
        min_length=2,
        max_length=6,
    )


class LessonAssessmentResponse(BaseModel):
    lesson_id: str = Field(
        min_length=1,
        max_length=100,
    )

    curriculum_id: str = Field(
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    questions: list[AssessmentQuestionResponse]


class AssessmentAnswerSubmission(BaseModel):
    question_id: str = Field(
        min_length=1,
        max_length=50,
    )

    selected_option: int = Field(
        ge=0,
        le=5,
    )


class LessonAssessmentSubmission(BaseModel):
    answers: list[AssessmentAnswerSubmission] = Field(
        min_length=1,
        max_length=20,
    )


class AssessmentQuestionResult(BaseModel):
    question_id: str

    selected_option: int

    is_correct: bool


class LessonAssessmentResultResponse(BaseModel):
    attempt_id: UUID

    lesson_id: str

    curriculum_id: str

    correct_answers: int = Field(
        ge=0,
    )

    total_questions: int = Field(
        ge=1,
    )

    score_percent: int = Field(
        ge=0,
        le=100,
    )

    recommendation: AssessmentRecommendation

    question_results: list[
        AssessmentQuestionResult
    ]

    created_at: datetime