from fastapi import APIRouter  # type: ignore

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "Healthy",
        "application": "A4A Learn",
        "version": "1.0.0",
    }