import uuid

from pydantic import BaseModel


class ISLPredictionResponse(BaseModel):
    label: str | None
    predicted_label: str | None
    confidence: float
    accepted: bool
    threshold: float
    model: str
    hand_detected: bool
    message: str

    attempt_id: uuid.UUID | None = None
    target_letter: str | None = None
    is_correct: bool | None = None

    # Runtime HITL workflow state.
    workflow_decision: str = "continue"
    escalation_reason: str = "normal"
    requires_human_review: bool = False
    review_id: uuid.UUID | None = None
