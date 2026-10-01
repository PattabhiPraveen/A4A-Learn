from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.lesson_assessment_attempt_repository import (
    LessonAssessmentAttemptRepository,
)
from app.schemas.assessment import (
    AssessmentQuestionResult,
    LessonAssessmentResultResponse,
    LessonAssessmentSubmission,
)
from app.services.assessment_content_service import (
    AssessmentContentService,
)


class AssessmentSubmissionError(ValueError):
    pass


class AssessmentService:
    """
    Deterministic lesson assessment service.

    The learner submits only question IDs and selected options.
    Correctness, score, recommendation and user ownership are
    calculated and enforced by the backend.
    """

    def __init__(
        self,
        db: Session,
        content_service: AssessmentContentService | None = None,
    ) -> None:
        self.db = db
        self.content_service = (
            content_service
            or AssessmentContentService()
        )
        self.repository = (
            LessonAssessmentAttemptRepository(db)
        )

    @staticmethod
    def _recommendation(
        score_percent: int,
    ) -> str:
        if score_percent < 60:
            return "review"

        if score_percent < 80:
            return "practice"

        return "continue"

    def submit(
        self,
        *,
        user_id: UUID,
        lesson_id: str,
        submission: LessonAssessmentSubmission,
    ) -> LessonAssessmentResultResponse:
        assessment = self.content_service.get_assessment(
            lesson_id
        )

        answer_key = self.content_service.get_answer_key(
            lesson_id
        )

        expected_question_ids = set(
            answer_key.keys()
        )

        if len(submission.answers) != len(
            expected_question_ids
        ):
            raise AssessmentSubmissionError(
                "Exactly five answers are required."
            )

        submitted_question_ids = [
            answer.question_id
            for answer in submission.answers
        ]

        if len(set(submitted_question_ids)) != len(
            submitted_question_ids
        ):
            raise AssessmentSubmissionError(
                "Duplicate question IDs are not allowed."
            )

        if set(submitted_question_ids) != (
            expected_question_ids
        ):
            raise AssessmentSubmissionError(
                "Submitted question IDs do not match "
                "the governed assessment."
            )

        question_lookup = {
            question.id: question
            for question in assessment.questions
        }

        results: list[
            AssessmentQuestionResult
        ] = []

        correct_answers = 0

        for answer in submission.answers:
            question = question_lookup[
                answer.question_id
            ]

            if answer.selected_option >= len(
                question.options
            ):
                raise AssessmentSubmissionError(
                    "Selected option is outside the "
                    "valid range."
                )

            is_correct = (
                answer.selected_option
                == answer_key[answer.question_id]
            )

            if is_correct:
                correct_answers += 1

            results.append(
                AssessmentQuestionResult(
                    question_id=answer.question_id,
                    selected_option=answer.selected_option,
                    is_correct=is_correct,
                )
            )

        total_questions = len(
            expected_question_ids
        )

        score_percent = round(
            correct_answers
            / total_questions
            * 100
        )

        recommendation = self._recommendation(
            score_percent
        )

        attempt = self.repository.create(
            user_id=user_id,
            lesson_id=assessment.lesson_id,
            curriculum_id=assessment.curriculum_id,
            correct_answers=correct_answers,
            total_questions=total_questions,
            score_percent=score_percent,
            recommendation=recommendation,
        )

        return LessonAssessmentResultResponse(
            attempt_id=attempt.id,
            lesson_id=attempt.lesson_id,
            curriculum_id=attempt.curriculum_id,
            correct_answers=attempt.correct_answers,
            total_questions=attempt.total_questions,
            score_percent=attempt.score_percent,
            recommendation=attempt.recommendation,
            question_results=results,
            created_at=attempt.created_at,
        )