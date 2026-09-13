import uuid

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.isl_practice_attempt import ISLPracticeAttempt


class ISLPracticeAttemptRepository:
    """
    Persistence and aggregation layer for ISL alphabet practice attempts.

    Responsibilities:
    - create practice attempts
    - retrieve learner attempts
    - provide database-level aggregate statistics

    Transaction ownership remains with the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        target_letter: str,
        predicted_letter: str | None,
        confidence: float | None,
        accepted: bool,
        is_correct: bool,
    ) -> ISLPracticeAttempt:

        attempt = ISLPracticeAttempt(
            user_id=user_id,
            target_letter=target_letter,
            predicted_letter=predicted_letter,
            confidence=confidence,
            accepted=accepted,
            is_correct=is_correct,
        )

        self.db.add(attempt)
        self.db.flush()
        self.db.refresh(attempt)

        return attempt

    def get_by_id(
        self,
        attempt_id: uuid.UUID,
    ) -> ISLPracticeAttempt | None:

        stmt = select(
            ISLPracticeAttempt
        ).where(
            ISLPracticeAttempt.id == attempt_id
        )

        return self.db.scalar(stmt)

    def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ISLPracticeAttempt]:

        stmt = (
            select(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id
            )
            .order_by(
                ISLPracticeAttempt.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def count_by_user(
        self,
        user_id: uuid.UUID,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id
            )
        )

        return int(
            self.db.scalar(stmt) or 0
        )

    def count_correct_by_user(
        self,
        user_id: uuid.UUID,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id,
                ISLPracticeAttempt.is_correct.is_(True),
            )
        )

        return int(
            self.db.scalar(stmt) or 0
        )

    def aggregate_by_letter(
        self,
        user_id: uuid.UUID,
    ) -> list[dict]:
        """
        Aggregate learner performance by target ISL letter.

        Returns one dictionary for every target letter the learner
        has attempted.

        Business interpretation such as weak/strong letters is
        intentionally left to the service layer.
        """

        stmt = (
            select(
                ISLPracticeAttempt.target_letter.label(
                    "target_letter"
                ),
                func.count(
                    ISLPracticeAttempt.id
                ).label(
                    "total_attempts"
                ),
                func.sum(
                    case(
                        (
                            ISLPracticeAttempt.is_correct.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "correct_attempts"
                ),
                func.sum(
                    case(
                        (
                            ISLPracticeAttempt.accepted.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label(
                    "accepted_attempts"
                ),
                func.avg(
                    ISLPracticeAttempt.confidence
                ).label(
                    "average_confidence"
                ),
            )
            .where(
                ISLPracticeAttempt.user_id == user_id
            )
            .group_by(
                ISLPracticeAttempt.target_letter
            )
            .order_by(
                ISLPracticeAttempt.target_letter
            )
        )

        rows = self.db.execute(stmt).all()

        return [
            {
                "target_letter": row.target_letter,
                "total_attempts": int(
                    row.total_attempts or 0
                ),
                "correct_attempts": int(
                    row.correct_attempts or 0
                ),
                "accepted_attempts": int(
                    row.accepted_attempts or 0
                ),
                "average_confidence": (
                    round(
                        float(row.average_confidence),
                        4,
                    )
                    if row.average_confidence is not None
                    else None
                ),
            }
            for row in rows
        ]

    def list_recent_by_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 10,
    ) -> list[ISLPracticeAttempt]:
        """
        Return the learner's most recent ISL practice attempts.
        """

        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        stmt = (
            select(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id
            )
            .order_by(
                ISLPracticeAttempt.created_at.desc(),
                ISLPracticeAttempt.id.desc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def count_low_confidence_by_user(
        self,
        user_id: uuid.UUID,
        *,
        threshold: float = 0.70,
    ) -> int:
        """
        Count attempts below the supplied confidence threshold.

        This is an evidence query only. It does not decide whether
        teacher intervention is required.
        """

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0.0 and 1.0."
            )

        stmt = (
            select(func.count())
            .select_from(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id,
                ISLPracticeAttempt.confidence.is_not(None),
                ISLPracticeAttempt.confidence < threshold,
            )
        )

        return int(
            self.db.scalar(stmt) or 0
        )

    def count_incorrect_by_letter(
        self,
        user_id: uuid.UUID,
        target_letter: str,
    ) -> int:
        """
        Count incorrect attempts for one target letter.

        Used later by the service/HITL layer to identify repeated
        learner difficulty.
        """

        stmt = (
            select(func.count())
            .select_from(ISLPracticeAttempt)
            .where(
                ISLPracticeAttempt.user_id == user_id,
                ISLPracticeAttempt.target_letter == target_letter,
                ISLPracticeAttempt.is_correct.is_(False),
            )
        )

        return int(
            self.db.scalar(stmt) or 0
        )