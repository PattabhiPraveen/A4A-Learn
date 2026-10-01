from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.assessment import (
    AssessmentQuestionResponse,
    LessonAssessmentResponse,
)


class AssessmentContentNotFoundError(Exception):
    pass


class AssessmentContentValidationError(Exception):
    pass


class AssessmentContentService:
    """
    Loads governed learner assessments from DS004.

    Answer keys remain internal to this service and are never
    included in learner-facing assessment responses.
    """

    def __init__(
        self,
        registry_path: Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[3]

        self.registry_path = (
            registry_path
            or project_root
            / "datasets"
            / "raw"
            / "DS004_Assessments"
            / "quizzes"
            / "mvp_quizzes.json"
        )

    def _load_registry(self) -> dict[str, Any]:
        if not self.registry_path.is_file():
            raise AssessmentContentNotFoundError(
                "Governed assessment registry was not found."
            )

        try:
            payload = json.loads(
                self.registry_path.read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise AssessmentContentValidationError(
                "Governed assessment registry could not be read."
            ) from exc

        if payload.get("dataset_id") != "DS004_Assessments":
            raise AssessmentContentValidationError(
                "Unexpected assessment dataset identifier."
            )

        assessments = payload.get("assessments")

        if not isinstance(assessments, list):
            raise AssessmentContentValidationError(
                "Assessment registry must contain assessments."
            )

        return payload

    def _get_raw_assessment(
        self,
        lesson_id: str,
    ) -> dict[str, Any]:
        registry = self._load_registry()

        matches = [
            assessment
            for assessment in registry["assessments"]
            if assessment.get("lesson_id") == lesson_id
        ]

        if not matches:
            raise AssessmentContentNotFoundError(
                f"No assessment is registered for {lesson_id}."
            )

        if len(matches) != 1:
            raise AssessmentContentValidationError(
                f"Multiple assessments are registered for {lesson_id}."
            )

        assessment = matches[0]

        self._validate_assessment(assessment)

        return assessment

    def _validate_assessment(
        self,
        assessment: dict[str, Any],
    ) -> None:
        required_fields = (
            "lesson_id",
            "curriculum_id",
            "title",
            "questions",
        )

        for field in required_fields:
            if field not in assessment:
                raise AssessmentContentValidationError(
                    f"Assessment is missing field: {field}."
                )

        questions = assessment["questions"]

        if not isinstance(questions, list):
            raise AssessmentContentValidationError(
                "Assessment questions must be a list."
            )

        if len(questions) != 5:
            raise AssessmentContentValidationError(
                "MVP assessments must contain exactly five questions."
            )

        question_ids: set[str] = set()

        for question in questions:
            self._validate_question(question)

            question_id = question["id"]

            if question_id in question_ids:
                raise AssessmentContentValidationError(
                    f"Duplicate question ID: {question_id}."
                )

            question_ids.add(question_id)

    def _validate_question(
        self,
        question: dict[str, Any],
    ) -> None:
        required_fields = (
            "id",
            "question",
            "options",
            "correct_option",
        )

        for field in required_fields:
            if field not in question:
                raise AssessmentContentValidationError(
                    f"Question is missing field: {field}."
                )

        options = question["options"]

        if not isinstance(options, list):
            raise AssessmentContentValidationError(
                "Question options must be a list."
            )

        if len(options) != 4:
            raise AssessmentContentValidationError(
                "MVP questions must contain exactly four options."
            )

        correct_option = question["correct_option"]

        if (
            not isinstance(correct_option, int)
            or isinstance(correct_option, bool)
            or correct_option < 0
            or correct_option >= len(options)
        ):
            raise AssessmentContentValidationError(
                f"Invalid answer key for question {question['id']}."
            )

    def get_assessment(
        self,
        lesson_id: str,
    ) -> LessonAssessmentResponse:
        """
        Return the learner-safe assessment.

        correct_option is deliberately omitted.
        """

        assessment = self._get_raw_assessment(
            lesson_id
        )

        questions = [
            AssessmentQuestionResponse(
                id=question["id"],
                question=question["question"],
                options=question["options"],
            )
            for question in assessment["questions"]
        ]

        return LessonAssessmentResponse(
            lesson_id=assessment["lesson_id"],
            curriculum_id=assessment["curriculum_id"],
            title=assessment["title"],
            questions=questions,
        )

    def get_answer_key(
        self,
        lesson_id: str,
    ) -> dict[str, int]:
        """
        Internal scoring contract.

        This method must never be returned directly by an API.
        """

        assessment = self._get_raw_assessment(
            lesson_id
        )

        return {
            question["id"]: question["correct_option"]
            for question in assessment["questions"]
        }