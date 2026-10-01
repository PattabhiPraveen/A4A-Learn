from dataclasses import dataclass

from app.services.learning_content_service import (
    LearningContentNotFoundError,
    LearningContentService,
)


@dataclass(frozen=True)
class LessonRAGContext:
    """
    Trusted lesson context resolved from governed curriculum content.

    The client supplies only a lesson identifier. Lesson content is
    always loaded server-side from LearningContentService.
    """

    lesson_id: str
    curriculum_id: str
    title: str
    course: str
    level: str
    content: str

    def as_retrieval_result(self) -> dict:
        """
        Represent the governed lesson as a RAG-compatible evidence item.

        Distance 0.0 indicates explicitly selected governed lesson
        context rather than a vector-similarity measurement.
        """

        return {
            "document": self.content,
            "distance": 0.0,
            "metadata": {
                "title": self.title,
                "source": self.lesson_id,
                "curriculum_id": self.curriculum_id,
                "course": self.course,
                "level": self.level,
                "evidence_scope": "selected_lesson",
            },
        }


class LessonContextResolver:
    """
    Resolves an optional client lesson identifier against governed
    server-side learning content.
    """

    def __init__(
        self,
        learning_content_service: LearningContentService | None = None,
    ) -> None:
        self.learning_content_service = (
            learning_content_service
            if learning_content_service is not None
            else LearningContentService()
        )

    def resolve(
        self,
        lesson_id: str | None,
    ) -> LessonRAGContext | None:
        """
        Return trusted lesson context when lesson_id is supplied.

        Missing lesson_id means the Tutor remains in general RAG mode.

        Invalid or unknown lesson identifiers are rejected rather than
        silently falling back to general RAG.
        """

        if lesson_id is None:
            return None

        normalized_lesson_id = lesson_id.strip()

        if not normalized_lesson_id:
            return None

        lesson = self.learning_content_service.get_lesson(
            normalized_lesson_id
        )

        return LessonRAGContext(
            lesson_id=lesson.id,
            curriculum_id=lesson.curriculum_id,
            title=lesson.title,
            course=lesson.course,
            level=lesson.level,
            content=lesson.content,
        )


__all__ = [
    "LearningContentNotFoundError",
    "LessonContextResolver",
    "LessonRAGContext",
]