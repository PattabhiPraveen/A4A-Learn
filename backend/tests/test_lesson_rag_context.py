from types import SimpleNamespace

import pytest

from app.rag.lesson_context import (
    LearningContentNotFoundError,
    LessonContextResolver,
    LessonRAGContext,
)


class FakeLearningContentService:
    def __init__(self) -> None:
        self.requested_lesson_id = None

    def get_lesson(self, lesson_id: str):
        self.requested_lesson_id = lesson_id

        if lesson_id == "lesson_9999":
            raise LearningContentNotFoundError(
                lesson_id
            )

        return SimpleNamespace(
            id="lesson_01",
            curriculum_id="PY-01",
            title="Introduction to Python",
            course="Python",
            level="Beginner",
            content="Python is a programming language.",
        )


def test_no_lesson_id_returns_none():
    service = FakeLearningContentService()

    resolver = LessonContextResolver(
        learning_content_service=service
    )

    assert resolver.resolve(None) is None
    assert service.requested_lesson_id is None


def test_blank_lesson_id_returns_none():
    service = FakeLearningContentService()

    resolver = LessonContextResolver(
        learning_content_service=service
    )

    assert resolver.resolve("   ") is None
    assert service.requested_lesson_id is None


def test_lesson_is_resolved_server_side():
    service = FakeLearningContentService()

    resolver = LessonContextResolver(
        learning_content_service=service
    )

    context = resolver.resolve(
        " lesson_01 "
    )

    assert isinstance(
        context,
        LessonRAGContext,
    )

    assert service.requested_lesson_id == "lesson_01"

    assert context.lesson_id == "lesson_01"
    assert context.curriculum_id == "PY-01"
    assert context.title == "Introduction to Python"
    assert context.course == "Python"
    assert context.level == "Beginner"

    assert (
        context.content
        == "Python is a programming language."
    )


def test_lesson_context_becomes_rag_evidence():
    service = FakeLearningContentService()

    resolver = LessonContextResolver(
        learning_content_service=service
    )

    context = resolver.resolve(
        "lesson_01"
    )

    assert context is not None

    evidence = context.as_retrieval_result()

    assert (
        evidence["document"]
        == "Python is a programming language."
    )

    assert evidence["distance"] == 0.0

    assert (
        evidence["metadata"]["title"]
        == "Introduction to Python"
    )

    assert (
        evidence["metadata"]["source"]
        == "lesson_01"
    )

    assert (
        evidence["metadata"]["curriculum_id"]
        == "PY-01"
    )

    assert (
        evidence["metadata"]["evidence_scope"]
        == "selected_lesson"
    )


def test_unknown_lesson_is_not_silently_accepted():
    service = FakeLearningContentService()

    resolver = LessonContextResolver(
        learning_content_service=service
    )

    with pytest.raises(
        LearningContentNotFoundError
    ):
        resolver.resolve(
            "lesson_9999"
        )