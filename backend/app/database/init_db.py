from app.database.database import engine
from app.database.base import Base


def init_db():
    Base.metadata.create_all(bind=engine)