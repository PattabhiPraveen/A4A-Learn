from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.constants import APP_DESCRIPTION
from app.core.logging import logger


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=APP_DESCRIPTION,
)


# =========================================================
# CORS
# =========================================================

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

cors_methods = [
    method.strip()
    for method in settings.CORS_ALLOW_METHODS.split(",")
    if method.strip()
]

cors_headers = [
    header.strip()
    for header in settings.CORS_ALLOW_HEADERS.split(",")
    if header.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)


# =========================================================
# API ROUTES
# =========================================================

app.include_router(api_router)


# =========================================================
# APPLICATION LIFECYCLE
# =========================================================

@app.on_event("startup")
async def startup():
    logger.info("Starting A4A Learn Backend...")

    # Database initialization is intentionally
    # controlled outside application startup.
    # init_db()

    logger.info("Database Initialized")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping A4A Learn Backend...")