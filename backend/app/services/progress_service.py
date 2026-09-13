import uuid

from sqlalchemy.orm import Session

from app.models.isl_practice_attempt import ISLPracticeAttempt
from app.repositories.isl_practice_attempt_repository import (
    ISLPracticeAttemptRepository,
)


class ProgressService:
    """
    Business service for learner ISL practice progress.

    Responsibilities:
    - validate practice input
    - derive correctness on the server
    - persist attempts
    - calculate learner progress statistics
    - calculate per-letter performance facts
    - calculate detailed learner analytics
    - identify provisional weak-letter learning signals
    - own the database transaction boundary

    ProgressService provides learner evidence only.

    Runtime escalation decisions remain the responsibility
    of EscalationPolicy / LearningReviewService.
    """

    VALID_ISL_LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Provisional MVP analytics thresholds.
    # These are learning signals, not diagnostic or
    # automatic teacher-intervention decisions.
    WEAK_LETTER_MIN_ATTEMPTS = 3
    WEAK_LETTER_ACCURACY_THRESHOLD = 60.0
    LOW_CONFIDENCE_THRESHOLD = 0.70

    def __init__(self, db: Session):
        self.db = db
        self.attempt_repository = (
            ISLPracticeAttemptRepository(db)
        )

    @staticmethod
    def _normalize_letter(
        letter: str | None,
    ) -> str | None:
        """
        Normalize an ISL alphabet letter.

        Examples:
        - "a" -> "A"
        - " A " -> "A"
        - empty input -> None
        """

        if letter is None:
            return None

        normalized = letter.strip().upper()

        if not normalized:
            return None

        return normalized

    def _validate_target_letter(
        self,
        target_letter: str,
    ) -> str:
        """
        Validate and normalize the learner's target letter.
        """

        normalized = self._normalize_letter(
            target_letter
        )

        if (
            normalized is None
            or len(normalized) != 1
            or normalized not in self.VALID_ISL_LETTERS
        ):
            raise ValueError(
                "target_letter must be a single letter from A to Z."
            )

        return normalized

    def _validate_predicted_letter(
        self,
        predicted_letter: str | None,
    ) -> str | None:
        """
        Validate and normalize the model-predicted letter.
        """

        normalized = self._normalize_letter(
            predicted_letter
        )

        if normalized is None:
            return None

        if (
            len(normalized) != 1
            or normalized not in self.VALID_ISL_LETTERS
        ):
            raise ValueError(
                "predicted_letter must be a single letter from A to Z."
            )

        return normalized

    @staticmethod
    def _validate_confidence(
        confidence: float | None,
    ) -> float | None:
        """
        Validate model confidence.

        Confidence must be between 0.0 and 1.0.
        """

        if confidence is None:
            return None

        confidence = float(confidence)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0."
            )

        return confidence

    def record_isl_attempt(
        self,
        *,
        user_id: uuid.UUID,
        target_letter: str,
        predicted_letter: str | None,
        confidence: float | None,
        accepted: bool,
    ) -> ISLPracticeAttempt:
        """
        Record one ISL alphabet practice attempt.

        The backend derives is_correct.
        Clients cannot provide is_correct.

        Correctness rule:

        accepted
        AND
        normalized target == normalized prediction
        """

        target = self._validate_target_letter(
            target_letter
        )

        predicted = self._validate_predicted_letter(
            predicted_letter
        )

        confidence = self._validate_confidence(
            confidence
        )

        accepted = bool(accepted)

        is_correct = bool(
            accepted
            and predicted is not None
            and target == predicted
        )

        try:
            attempt = (
                self.attempt_repository.create(
                    user_id=user_id,
                    target_letter=target,
                    predicted_letter=predicted,
                    confidence=confidence,
                    accepted=accepted,
                    is_correct=is_correct,
                )
            )

            self.db.commit()
            self.db.refresh(attempt)

            return attempt

        except Exception:
            self.db.rollback()
            raise

    def get_user_progress(
        self,
        user_id: uuid.UUID,
    ) -> dict:
        """
        Return basic learner progress statistics.

        MVP metrics:
        - total attempts
        - correct attempts
        - incorrect attempts
        - accuracy percentage
        """

        total_attempts = (
            self.attempt_repository.count_by_user(
                user_id
            )
        )

        correct_attempts = (
            self.attempt_repository
            .count_correct_by_user(
                user_id
            )
        )

        incorrect_attempts = (
            total_attempts - correct_attempts
        )

        accuracy_percent = (
            round(
                (
                    correct_attempts
                    / total_attempts
                )
                * 100,
                2,
            )
            if total_attempts > 0
            else 0.0
        )

        return {
            "user_id": str(user_id),
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "incorrect_attempts": (
                incorrect_attempts
            ),
            "accuracy_percent": (
                accuracy_percent
            ),
        }

    def get_letter_performance(
        self,
        user_id: uuid.UUID,
        target_letter: str,
    ) -> dict:
        """
        Return learner performance facts for one ISL letter.

        This method intentionally returns evidence only.
        It does not decide whether a learner requires
        retry or teacher review.

        Runtime workflow decisions belong to
        EscalationPolicy / LearningReviewService.
        """

        target = self._validate_target_letter(
            target_letter
        )

        letter_rows = (
            self.attempt_repository
            .aggregate_by_letter(
                user_id
            )
        )

        for row in letter_rows:
            if row["target_letter"] != target:
                continue

            total = row[
                "total_attempts"
            ]

            correct = row[
                "correct_attempts"
            ]

            accepted = row[
                "accepted_attempts"
            ]

            accuracy_percent = (
                round(
                    (
                        correct
                        / total
                    )
                    * 100,
                    2,
                )
                if total > 0
                else 0.0
            )

            acceptance_rate_percent = (
                round(
                    (
                        accepted
                        / total
                    )
                    * 100,
                    2,
                )
                if total > 0
                else 0.0
            )

            return {
                "target_letter": target,
                "total_attempts": total,
                "correct_attempts": correct,
                "incorrect_attempts": (
                    total - correct
                ),
                "accepted_attempts": accepted,
                "accuracy_percent": (
                    accuracy_percent
                ),
                "acceptance_rate_percent": (
                    acceptance_rate_percent
                ),
                "average_confidence": row[
                    "average_confidence"
                ],
            }

        return {
            "target_letter": target,
            "total_attempts": 0,
            "correct_attempts": 0,
            "incorrect_attempts": 0,
            "accepted_attempts": 0,
            "accuracy_percent": 0.0,
            "acceptance_rate_percent": 0.0,
            "average_confidence": None,
        }

    def get_user_analytics(
        self,
        user_id: uuid.UUID,
        *,
        recent_limit: int = 10,
    ) -> dict:
        """
        Return detailed ISL learner analytics.

        Includes:
        - overall learner progress
        - per-letter performance
        - acceptance rate
        - average model confidence
        - provisional weak-letter signals
        - low-confidence attempt count
        - recent attempts

        Weak-letter identification is an MVP learning
        signal only.

        It does not automatically trigger teacher
        intervention.
        """

        if (
            recent_limit < 1
            or recent_limit > 50
        ):
            raise ValueError(
                "recent_limit must be between 1 and 50."
            )

        overall = self.get_user_progress(
            user_id
        )

        letter_rows = (
            self.attempt_repository
            .aggregate_by_letter(
                user_id
            )
        )

        letter_performance = []
        weak_letters = []

        for row in letter_rows:
            total = row[
                "total_attempts"
            ]

            correct = row[
                "correct_attempts"
            ]

            accepted = row[
                "accepted_attempts"
            ]

            accuracy_percent = (
                round(
                    (
                        correct
                        / total
                    )
                    * 100,
                    2,
                )
                if total > 0
                else 0.0
            )

            acceptance_rate_percent = (
                round(
                    (
                        accepted
                        / total
                    )
                    * 100,
                    2,
                )
                if total > 0
                else 0.0
            )

            is_weak_candidate = (
                total
                >= self.WEAK_LETTER_MIN_ATTEMPTS
                and accuracy_percent
                < self.WEAK_LETTER_ACCURACY_THRESHOLD
            )

            letter_result = {
                "target_letter": row[
                    "target_letter"
                ],
                "total_attempts": total,
                "correct_attempts": correct,
                "incorrect_attempts": (
                    total - correct
                ),
                "accepted_attempts": (
                    accepted
                ),
                "accuracy_percent": (
                    accuracy_percent
                ),
                "acceptance_rate_percent": (
                    acceptance_rate_percent
                ),
                "average_confidence": row[
                    "average_confidence"
                ],
                "weak_candidate": (
                    is_weak_candidate
                ),
            }

            letter_performance.append(
                letter_result
            )

            if is_weak_candidate:
                weak_letters.append(
                    {
                        "target_letter": row[
                            "target_letter"
                        ],
                        "total_attempts": (
                            total
                        ),
                        "accuracy_percent": (
                            accuracy_percent
                        ),
                        "average_confidence": row[
                            "average_confidence"
                        ],
                        "reason": (
                            "Repeated attempts with "
                            "accuracy below the "
                            "provisional MVP threshold."
                        ),
                    }
                )

        low_confidence_attempts = (
            self.attempt_repository
            .count_low_confidence_by_user(
                user_id,
                threshold=(
                    self.LOW_CONFIDENCE_THRESHOLD
                ),
            )
        )

        recent_attempts = (
            self.attempt_repository
            .list_recent_by_user(
                user_id,
                limit=recent_limit,
            )
        )

        recent_results = [
            {
                "id": str(
                    attempt.id
                ),
                "target_letter": (
                    attempt.target_letter
                ),
                "predicted_letter": (
                    attempt.predicted_letter
                ),
                "confidence": (
                    attempt.confidence
                ),
                "accepted": (
                    attempt.accepted
                ),
                "is_correct": (
                    attempt.is_correct
                ),
                "created_at": (
                    attempt.created_at
                ),
            }
            for attempt in recent_attempts
        ]

        return {
            "user_id": str(user_id),
            "overall": overall,
            "letters_attempted": len(
                letter_performance
            ),
            "letter_performance": (
                letter_performance
            ),
            "weak_letters": (
                weak_letters
            ),
            "weak_letter_count": len(
                weak_letters
            ),
            "low_confidence_attempts": (
                low_confidence_attempts
            ),
            "low_confidence_threshold": (
                self.LOW_CONFIDENCE_THRESHOLD
            ),
            "recent_attempts": (
                recent_results
            ),
        }
