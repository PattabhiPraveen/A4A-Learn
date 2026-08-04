from fastapi import APIRouter  # type: ignore

from app.api.routes.health import router as health_router
from app.api.routes.database import router as database_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(database_router)