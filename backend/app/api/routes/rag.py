import hashlib

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.rag.service import RAGService
from app.schemas.rag import (
    RAGQuestion,
    RAGResponse,
)
from app.services.learning_review_service import (
    LearningReviewService,
)


router = APIRouter(
    prefix="/rag",
    tags=["AI Tutor"],
)


rag_service = RAGService()


def _build_rag_activity_reference(
    question: str,
) -> str:
    """
    Build a deterministic, privacy-conscious reference
    for one normalized learner question.

    Repeating the same unanswered question while its
    review is pending reuses the existing review.

    The original question remains available in the
    governed review record as question_or_activity.
    """

    normalized = " ".join(
        question.strip().lower().split()
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:32]

    return f"rag:{digest}"


@router.post(
    "/ask",
    response_model=RAGResponse,
)
def ask_question(
    request: RAGQuestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Answer a learner question using curriculum-grounded RAG.

    Runtime governance:

    - grounded result:
        return the grounded answer
        and continue automatically

    - insufficient evidence:
        preserve the RAG abstention
        and create/reuse a teacher review

    The route does not invent a numeric RAG confidence.
    """

    try:
        rag_result = rag_service.answer(
            request.question
        )

        review_service = LearningReviewService(
            db
        )

        grounded = bool(
            rag_result["grounded"]
        )

        sources = rag_result.get(
            "sources",
            [],
        )

        # RAG evidence is represented by the existing
        # grounded flag and retrieved sources.
        #
        # No artificial numeric confidence is created.
        sufficient_evidence = bool(
            grounded and sources
        )

        activity_reference_id = (
            _build_rag_activity_reference(
                request.question
            )
        )

        retrieved_sources = (
            ", ".join(
                str(
                    source.get(
                        "title",
                        "Unknown source",
                    )
                )
                for source in sources
            )
            if sources
            else None
        )

        workflow = (
            review_service.evaluate_and_escalate(
                student_id=current_user.id,
                activity_type="rag",
                activity_reference_id=(
                    activity_reference_id
                ),
                question_or_activity=(
                    request.question.strip()
                ),
                ai_response=(
                    rag_result["answer"]
                ),
                retrieved_sources=(
                    retrieved_sources
                ),
                ai_confidence=None,
                sufficient_evidence=(
                    sufficient_evidence
                ),
                student_requested_help=False,
                consequential=False,
                attempt_count=0,
                accuracy_percent=None,
            )
        )

        review_id = (
            workflow.review.id
            if workflow.review is not None
            else None
        )

        return RAGResponse(
            question=rag_result["question"],
            answer=rag_result["answer"],
            grounded=grounded,
            sources=sources,
            workflow_decision=(
                workflow.decision.value
            ),
            escalation_reason=(
                workflow.reason
            ),
            requires_human_review=(
                workflow.requires_human_review
            ),
            review_id=review_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
