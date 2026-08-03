from fastapi import APIRouter  # type: ignore[import]

from app.api.routes.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)