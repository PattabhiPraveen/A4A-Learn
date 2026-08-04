from fastapi import FastAPI  # type: ignore[import]

from app.api import api_router
from app.core.config import settings
from app.core.constants import APP_DESCRIPTION
from app.core.logging import logger
from app.database.init_db import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=APP_DESCRIPTION,
)

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    logger.info("Starting A4A Learn Backend...")

    init_db()

    logger.info("Database Initialized")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping A4A Learn Backend...")