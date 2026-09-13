import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LearnerReviewRequest(BaseModel):
    """
    Explicit learner request for teacher assistance.
    Student identity is derived from the authenticated user.
    """

    model_config = ConfigDict(extra="forbid")

    activity_type: str = Field(
        min_length=1,
        max_length=50,
    )
    activity_reference_id: str | None = Field(
        default=None,
        max_length=100,
    )
    question_or_activity: str = Field(
        min_length=1,
        max_length=5000,
    )


class TeacherReviewResolveRequest(BaseModel):
    """
    Teacher resolution payload.

    reviewed_by, reviewed_at and status are controlled by
    the backend and cannot be supplied by the client.
    """

    model_config = ConfigDict(extra="forbid")

    teacher_feedback: str = Field(
        min_length=1,
        max_length=5000,
    )


class LearningReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID

    activity_type: str
    activity_reference_id: str | None

    question_or_activity: str

    ai_response: str | None
    retrieved_sources: str | None
    ai_confidence: float | None

    reason_for_escalation: str
    student_attempts: int | None

    status: str

    teacher_feedback: str | None
    reviewed_by: uuid.UUID | None

    created_at: datetime
    reviewed_at: datetime | None


class LearnerReviewRequestResponse(BaseModel):
    decision: str
    reason: str
    requires_human_review: bool

    review_created: bool
    review: LearningReviewResponse
