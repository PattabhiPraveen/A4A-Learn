from sqlalchemy import select  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]

from app.core.security import hash_password
from app.models.user import User


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
) -> User:

    user = User(
        full_name=full_name,
        email=email.lower(),
        password_hash=hash_password(password),
        role="student",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user