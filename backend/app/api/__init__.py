from fastapi import APIRouter  # type: ignore

from app.api.routes.health import router as health_router
from app.api.routes.database import router as database_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.rag import router as rag_router
from app.api.routes.isl import router as isl_router
from app.api.routes.progress import router as progress_router
from app.api.routes.reviews import router as reviews_router


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(database_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(rag_router)
api_router.include_router(isl_router)
api_router.include_router(progress_router)
api_router.include_router(reviews_router)
