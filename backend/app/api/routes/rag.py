from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.models.user import User
from app.rag.service import RAGService
from app.schemas.rag import (
    RAGQuestion,
    RAGResponse,
)


router = APIRouter(
    prefix="/rag",
    tags=["AI Tutor"],
)


rag_service = RAGService()


@router.post(
    "/ask",
    response_model=RAGResponse,
)
def ask_question(
    request: RAGQuestion,
    current_user: User = Depends(get_current_user),
):

    try:
        return rag_service.answer(
            request.question
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