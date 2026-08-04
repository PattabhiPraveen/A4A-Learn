from fastapi import APIRouter  # type: ignore[import]
from sqlalchemy import text  # type: ignore[import]

from app.database.database import engine

router = APIRouter(tags=["Database"])


@router.get("/database")
def database_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "database": "Connected"
        }

    except Exception as e:
        return {
            "database": "Disconnected",
            "error": str(e)
        }