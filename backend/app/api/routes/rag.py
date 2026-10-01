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
from app.services.learning_content_service import (
    LearningContentNotFoundError,
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

    An optional lesson_id allows the learner's explicitly selected
    governed lesson to be considered first by the RAG service.

    The client supplies only the lesson identifier. Trusted lesson
    content is resolved server-side by the governed learning-content
    service.

    Runtime governance:

    - grounded result:
        return the grounded answer
        and continue automatically

    - insufficient evidence:
        preserve the RAG abstention
        and create/reuse a teacher review

    The route does not invent a numeric RAG confidence.

    Backward compatibility:

    - requests without lesson_id use the original
      rag_service.answer(question) invocation

    - requests with lesson_id use the new lesson-aware
      rag_service.answer(question, lesson_id=...) invocation
    """

    try:
        # -----------------------------------------
        # 1. Execute RAG
        # -----------------------------------------
        #
        # Preserve the original invocation contract
        # when lesson_id is absent.
        #
        # This keeps existing clients, tests, and
        # general Tutor behavior backward compatible.
        # -----------------------------------------

        if request.lesson_id is None:
            rag_result = rag_service.answer(
                request.question
            )
        else:
            rag_result = rag_service.answer(
                request.question,
                lesson_id=request.lesson_id,
            )

        # -----------------------------------------
        # 2. Initialize HITL governance
        # -----------------------------------------

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

        # -----------------------------------------
        # 3. Determine evidence sufficiency
        # -----------------------------------------
        #
        # A result is considered sufficiently
        # evidenced only when:
        #
        # - the RAG service reports it grounded
        # - at least one evidence source exists
        #
        # No artificial numeric confidence is
        # generated.
        # -----------------------------------------

        sufficient_evidence = bool(
            grounded and sources
        )

        # -----------------------------------------
        # 4. Build privacy-conscious activity ID
        # -----------------------------------------

        activity_reference_id = (
            _build_rag_activity_reference(
                request.question
            )
        )

        # -----------------------------------------
        # 5. Build source summary for review
        # -----------------------------------------

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

        # -----------------------------------------
        # 6. Evaluate HITL escalation
        # -----------------------------------------

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

        # -----------------------------------------
        # 7. Resolve optional review ID
        # -----------------------------------------

        review_id = (
            workflow.review.id
            if workflow.review is not None
            else None
        )

        # -----------------------------------------
        # 8. Return governed Tutor response
        # -----------------------------------------

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

    # ---------------------------------------------
    # Governed lesson does not exist
    # ---------------------------------------------
    #
    # Do not expose an internal server error when
    # the client supplies an unknown lesson ID.
    # ---------------------------------------------

    except LearningContentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    # ---------------------------------------------
    # Invalid RAG request
    # ---------------------------------------------

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # ---------------------------------------------
    # RAG runtime/service unavailable
    # ---------------------------------------------

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc