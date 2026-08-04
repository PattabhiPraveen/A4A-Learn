"""Database declarative Base.

Try to import DeclarativeBase from modern SQLAlchemy; fall back to the
older declarative_base() factory if the import isn't available so IDEs
or environments with different SQLAlchemy versions don't show unresolved
import errors.
"""
try:
    from sqlalchemy.orm import DeclarativeBase  # type: ignore

    class Base(DeclarativeBase):
        pass
except Exception:
    # Fallback for older SQLAlchemy versions
    # Fallback for older SQLAlchemy versions — use orm.declarative_base which
    # is available in newer and older installs instead of the removed
    # sqlalchemy.ext.declarative path.
    from sqlalchemy.orm import declarative_base  # type: ignore

    Base = declarative_base()