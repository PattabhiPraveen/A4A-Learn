import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ISLAttemptCreate(BaseModel):
    """
    Request schema for manually recording an ISL attempt.

    is_correct and user_id are intentionally excluded.
    They remain backend-controlled.
    """

    model_config = ConfigDict(extra="forbid")

    target_letter: str = Field(
        ...,
        min_length=1,
        max_length=1,
    )

    predicted_letter: str | None = Field(
        default=None,
        min_length=1,
        max_length=1,
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    accepted: bool


class ISLAttemptResponse(BaseModel):
    """
    Response for one persisted ISL practice attempt.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    target_letter: str
    predicted_letter: str | None
    confidence: float | None
    accepted: bool
    is_correct: bool
    created_at: datetime


class ProgressSummaryResponse(BaseModel):
    """
    Basic learner progress summary.
    """

    user_id: str
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    accuracy_percent: float


class LetterPerformanceResponse(BaseModel):
    """
    Aggregated performance for one target ISL letter.
    """

    target_letter: str

    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    accepted_attempts: int

    accuracy_percent: float
    acceptance_rate_percent: float

    average_confidence: float | None

    weak_candidate: bool


class WeakLetterResponse(BaseModel):
    """
    Provisional learner difficulty signal.

    This is not an automatic teacher-intervention decision.
    """

    target_letter: str
    total_attempts: int
    accuracy_percent: float
    average_confidence: float | None
    reason: str


class RecentAttemptResponse(BaseModel):
    """
    Recent ISL practice attempt included in analytics.
    """

    id: str
    target_letter: str
    predicted_letter: str | None
    confidence: float | None
    accepted: bool
    is_correct: bool
    created_at: datetime


class ProgressAnalyticsResponse(BaseModel):
    """
    Detailed authenticated learner analytics response.
    """

    user_id: str

    overall: ProgressSummaryResponse

    letters_attempted: int

    letter_performance: list[
        LetterPerformanceResponse
    ]

    weak_letters: list[
        WeakLetterResponse
    ]

    weak_letter_count: int

    low_confidence_attempts: int
    low_confidence_threshold: float

    recent_attempts: list[
        RecentAttemptResponse
    ]