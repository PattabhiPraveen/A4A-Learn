from pydantic import BaseModel, Field


class LearningLessonSummary(BaseModel):
    # Stable API/resource identifier derived from the filename,
    # for example: lesson_01.
    id: str = Field(..., min_length=1, max_length=100)

    # Curriculum identifier declared in governed lesson metadata,
    # for example: PY-01 or AI-01.
    curriculum_id: str = Field(..., min_length=1, max_length=50)

    title: str = Field(..., min_length=1, max_length=200)

    course: str = Field(..., min_length=1, max_length=100)

    level: str = Field(..., min_length=1, max_length=50)

    sequence: int = Field(..., ge=1)

    estimated_minutes: int = Field(..., ge=1, le=480)

    # Retained for API compatibility with the existing frontend.
    # For the governed curriculum this represents the course/topic area.
    topic: str = Field(..., min_length=1, max_length=100)

    description: str = Field(..., min_length=1, max_length=500)


class LearningLessonDetail(LearningLessonSummary):
    content: str = Field(..., min_length=1)
