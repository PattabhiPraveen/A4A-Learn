from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.isl.landmarks import HandLandmarkExtractor
from app.isl.predictor import ISLAlphabetPredictor
from app.models.user import User
from app.schemas.isl import ISLPredictionResponse
from app.services.learning_review_service import (
    LearningReviewService,
)
from app.services.progress_service import ProgressService


router = APIRouter(
    prefix="/isl",
    tags=["ISL Recognition"],
)


predictor = ISLAlphabetPredictor()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
}

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

MAX_FILE_SIZE = 10 * 1024 * 1024

CONFIDENCE_THRESHOLD = 0.70


def _evaluate_isl_workflow(
    *,
    db: Session,
    current_user: User,
    target: str,
    predicted_letter: str | None,
    confidence: float,
) -> tuple[str, str, bool, object | None]:
    """
    Evaluate the learner's current ISL practice state.

    ProgressService provides learner evidence.
    LearningReviewService applies the governed escalation
    policy and persists a review only when REVIEW is required.

    A stable activity reference is used per learner/letter,
    allowing an existing pending review to be reused.
    """

    progress_service = ProgressService(db)

    performance = (
        progress_service.get_letter_performance(
            user_id=current_user.id,
            target_letter=target,
        )
    )

    review_service = LearningReviewService(db)

    prediction_text = (
        predicted_letter
        if predicted_letter is not None
        else "No usable prediction"
    )

    workflow = (
        review_service.evaluate_and_escalate(
            student_id=current_user.id,
            activity_type="isl",
            activity_reference_id=f"isl:{target}",
            question_or_activity=(
                f"ISL alphabet practice for letter {target}"
            ),
            ai_response=(
                f"Predicted letter: {prediction_text}"
            ),
            ai_confidence=confidence,
            sufficient_evidence=True,
            student_requested_help=False,
            consequential=False,
            attempt_count=performance[
                "total_attempts"
            ],
            accuracy_percent=performance[
                "accuracy_percent"
            ],
        )
    )

    review_id = (
        workflow.review.id
        if workflow.review is not None
        else None
    )

    return (
        workflow.decision.value,
        workflow.reason,
        workflow.requires_human_review,
        review_id,
    )


@router.post(
    "/predict",
    response_model=ISLPredictionResponse,
)
async def predict_isl(
    target_letter: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Predict an ISL alphabet from an uploaded image.

    The learner supplies:
    - target_letter
    - image
    - authentication token

    The backend controls:
    - user_id
    - predicted label
    - confidence
    - accepted status
    - correctness
    - persistence
    - runtime escalation decision
    - human-review creation/reuse
    """

    progress_service = ProgressService(db)

    # Validate and normalize the learner's target.
    try:
        target = (
            progress_service._validate_target_letter(
                target_letter
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only JPEG and PNG images are supported.",
        )

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image file extension.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 10 MB limit.",
        )

    temp_path = None

    try:
        with NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(content)

            temp_path = Path(
                temp_file.name
            )

        extractor = HandLandmarkExtractor()

        try:
            features = extractor.extract(
                str(temp_path)
            )
        finally:
            extractor.close()

        # No usable hand landmarks.
        #
        # Persist the failed attempt first. The workflow
        # policy then evaluates the learner's updated
        # target-letter history.
        if features is None:
            attempt = (
                progress_service.record_isl_attempt(
                    user_id=current_user.id,
                    target_letter=target,
                    predicted_letter=None,
                    confidence=0.0,
                    accepted=False,
                )
            )

            (
                workflow_decision,
                escalation_reason,
                requires_human_review,
                review_id,
            ) = _evaluate_isl_workflow(
                db=db,
                current_user=current_user,
                target=target,
                predicted_letter=None,
                confidence=0.0,
            )

            if requires_human_review:
                message = (
                    "Repeated difficulty was detected "
                    f"while practising {target}. "
                    "A teacher review has been requested."
                )
            else:
                message = (
                    "No hand detected. "
                    "Please reposition your hand and try again."
                )

            return ISLPredictionResponse(
                label=None,
                predicted_label=None,
                confidence=0.0,
                accepted=False,
                threshold=CONFIDENCE_THRESHOLD,
                model=predictor.model_name,
                hand_detected=False,
                message=message,
                attempt_id=attempt.id,
                target_letter=attempt.target_letter,
                is_correct=attempt.is_correct,
                workflow_decision=workflow_decision,
                escalation_reason=escalation_reason,
                requires_human_review=(
                    requires_human_review
                ),
                review_id=review_id,
            )

        result = predictor.predict(
            features,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )

        # IMPORTANT:
        # Persist the model's actual predicted_label rather
        # than the accepted label. This preserves
        # low-confidence evidence for progress analytics
        # and governed HITL decisions.
        attempt = (
            progress_service.record_isl_attempt(
                user_id=current_user.id,
                target_letter=target,
                predicted_letter=result[
                    "predicted_label"
                ],
                confidence=result[
                    "confidence"
                ],
                accepted=result[
                    "accepted"
                ],
            )
        )

        (
            workflow_decision,
            escalation_reason,
            requires_human_review,
            review_id,
        ) = _evaluate_isl_workflow(
            db=db,
            current_user=current_user,
            target=target,
            predicted_letter=result[
                "predicted_label"
            ],
            confidence=result[
                "confidence"
            ],
        )

        if requires_human_review:
            message = (
                "Repeated difficulty was detected "
                f"while practising {target}. "
                "A teacher review has been requested."
            )

        elif workflow_decision == "retry":
            message = (
                "The prediction confidence is too low. "
                "Please reposition your hand and try again."
            )

        elif result["accepted"]:
            if attempt.is_correct:
                message = (
                    "Correct. Detected ISL alphabet: "
                    f"{result['label']}"
                )
            else:
                message = (
                    "Detected ISL alphabet: "
                    f"{result['label']}. "
                    f"Please try {target} again."
                )

        else:
            message = (
                "Please reposition your hand and try again."
            )

        return ISLPredictionResponse(
            **result,
            hand_detected=True,
            message=message,
            attempt_id=attempt.id,
            target_letter=attempt.target_letter,
            is_correct=attempt.is_correct,
            workflow_decision=workflow_decision,
            escalation_reason=escalation_reason,
            requires_human_review=(
                requires_human_review
            ),
            review_id=review_id,
        )

    finally:
        if (
            temp_path is not None
            and temp_path.exists()
        ):
            temp_path.unlink(
                missing_ok=True
            )
