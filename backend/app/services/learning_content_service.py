from __future__ import annotations

import re
from pathlib import Path

from app.schemas.learning import (
    LearningLessonDetail,
    LearningLessonSummary,
)


class LearningContentNotFoundError(Exception):
    """Raised when a requested learning lesson does not exist."""


class LearningContentMetadataError(ValueError):
    """Raised when governed lesson metadata is missing or invalid."""


class LearningContentService:
    """
    Reads approved learner-facing educational content from DS001_Education.

    Only the mvp_test directory is exposed to the learner application.
    Benchmark/evaluation documents are intentionally excluded.

    Each governed lesson uses controlled front matter such as:

        ---
        id: PY-01
        course: Python
        level: Beginner
        sequence: 1
        estimated_minutes: 15
        ---

    The filename remains the stable API resource identifier
    (for example lesson_01), while the metadata id represents the
    curriculum identifier (for example PY-01).
    """

    REQUIRED_METADATA = {
        "id",
        "course",
        "level",
        "sequence",
        "estimated_minutes",
    }

    SUPPORTED_COURSES = {
        "Python",
        "Artificial Intelligence",
    }

    def __init__(self, content_root: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[3]

        self.content_root = (
            content_root
            if content_root is not None
            else project_root
            / "datasets"
            / "raw"
            / "DS001_Education"
            / "mvp_test"
        )

    @classmethod
    def _parse_front_matter(
        cls,
        markdown: str,
        filename: str,
    ) -> tuple[dict[str, str], str]:
        """
        Parse the controlled lesson front matter.

        This intentionally avoids an external YAML dependency because
        the MVP lesson metadata contract contains only simple key/value
        fields.

        Returns:
            A tuple containing:
            - parsed metadata
            - Markdown lesson body
        """
        normalized = markdown.lstrip("\ufeff")
        lines = normalized.splitlines()

        if not lines or lines[0].strip() != "---":
            raise LearningContentMetadataError(
                f"Missing front matter in learning content: {filename}"
            )

        closing_index: int | None = None

        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                closing_index = index
                break

        if closing_index is None:
            raise LearningContentMetadataError(
                f"Unclosed front matter in learning content: {filename}"
            )

        metadata: dict[str, str] = {}

        for line in lines[1:closing_index]:
            stripped = line.strip()

            if not stripped:
                continue

            if ":" not in stripped:
                raise LearningContentMetadataError(
                    f"Invalid metadata line in {filename}: {stripped}"
                )

            key, value = stripped.split(":", 1)

            key = key.strip()
            value = value.strip()

            if not key or not value:
                raise LearningContentMetadataError(
                    f"Invalid metadata field in {filename}: {stripped}"
                )

            if key in metadata:
                raise LearningContentMetadataError(
                    f"Duplicate metadata field '{key}' in {filename}"
                )

            metadata[key] = value

        missing = cls.REQUIRED_METADATA - metadata.keys()

        if missing:
            missing_fields = ", ".join(sorted(missing))

            raise LearningContentMetadataError(
                f"Missing metadata field(s) in {filename}: "
                f"{missing_fields}"
            )

        body = "\n".join(
            lines[closing_index + 1 :]
        ).strip()

        if not body:
            raise LearningContentMetadataError(
                f"Learning content file contains no lesson body: "
                f"{filename}"
            )

        return metadata, body

    @classmethod
    def _validate_metadata(
        cls,
        metadata: dict[str, str],
        filename: str,
    ) -> tuple[str, str, str, int, int]:
        """
        Validate governed curriculum metadata and return normalized values.
        """
        curriculum_id = metadata["id"].strip().upper()
        course = metadata["course"].strip()
        level = metadata["level"].strip()

        if not re.fullmatch(
            r"(?:PY|AI)-[0-9]{2,3}",
            curriculum_id,
        ):
            raise LearningContentMetadataError(
                f"Invalid curriculum id in {filename}: "
                f"{curriculum_id}"
            )

        if course not in cls.SUPPORTED_COURSES:
            raise LearningContentMetadataError(
                f"Unsupported course in {filename}: {course}"
            )

        if not level:
            raise LearningContentMetadataError(
                f"Missing learning level in {filename}"
            )

        try:
            sequence = int(metadata["sequence"])
        except ValueError as exc:
            raise LearningContentMetadataError(
                f"Invalid sequence in {filename}"
            ) from exc

        try:
            estimated_minutes = int(
                metadata["estimated_minutes"]
            )
        except ValueError as exc:
            raise LearningContentMetadataError(
                f"Invalid estimated_minutes in {filename}"
            ) from exc

        if sequence < 1:
            raise LearningContentMetadataError(
                f"Sequence must be at least 1 in {filename}"
            )

        if not 1 <= estimated_minutes <= 480:
            raise LearningContentMetadataError(
                f"estimated_minutes must be between 1 and 480 "
                f"in {filename}"
            )

        expected_prefix = (
            "PY-"
            if course == "Python"
            else "AI-"
        )

        if not curriculum_id.startswith(expected_prefix):
            raise LearningContentMetadataError(
                f"Curriculum id {curriculum_id} does not match "
                f"course {course} in {filename}"
            )

        return (
            curriculum_id,
            course,
            level,
            sequence,
            estimated_minutes,
        )

    @staticmethod
    def _extract_title(
        markdown: str,
        fallback: str,
    ) -> str:
        """
        Extract the first H1 Markdown heading as the lesson title.
        """
        for line in markdown.splitlines():
            stripped = line.strip()

            # Support both "# Title" and "\# Title".
            stripped = stripped.removeprefix("\\")

            if stripped.startswith("# "):
                title = stripped[2:].strip()

                if title:
                    return title

        return fallback

    @staticmethod
    def _clean_content(markdown: str) -> str:
        """
        Remove the first Markdown H1 heading because the title is
        returned separately by the API.

        Preserve the remainder of the lesson Markdown.
        """
        lines = markdown.splitlines()

        cleaned_lines: list[str] = []
        heading_removed = False

        for line in lines:
            candidate = (
                line.strip()
                .removeprefix("\\")
            )

            if (
                not heading_removed
                and candidate.startswith("# ")
            ):
                heading_removed = True
                continue

            cleaned_lines.append(line)

        content = "\n".join(
            cleaned_lines
        ).strip()

        # Collapse excessive blank lines while preserving normal
        # paragraph separation.
        content = re.sub(
            r"\n\s*\n\s*\n+",
            "\n\n",
            content,
        )

        return content

    @staticmethod
    def _build_description(
        content: str,
        max_length: int = 220,
    ) -> str:
        """
        Build a concise lesson description from the lesson body.
        """
        normalized = " ".join(
            content.split()
        )

        if len(normalized) <= max_length:
            return normalized

        # Reserve three characters for an ASCII ellipsis.
        # This avoids the earlier Windows encoding/mojibake issue.
        shortened = normalized[
            : max_length - 3
        ].rstrip()

        if " " in shortened:
            shortened = shortened.rsplit(
                " ",
                1,
            )[0]

        return f"{shortened}..."

    @staticmethod
    def _topic_for_course(
        course: str,
    ) -> str:
        """
        Preserve the existing topic API field while aligning it with
        the governed technical curriculum.
        """
        return course

    def _lesson_files(self) -> list[Path]:
        """
        Return only approved lesson files from the governed MVP directory.
        """
        if not self.content_root.exists():
            return []

        return sorted(
            path
            for path in self.content_root.glob(
                "lesson_*.md"
            )
            if path.is_file()
        )

    def _read_lesson(
        self,
        path: Path,
    ) -> LearningLessonDetail:
        """
        Read, validate and convert one governed lesson into the API model.
        """
        raw_markdown = path.read_text(
            encoding="utf-8-sig"
        )

        metadata, markdown_body = (
            self._parse_front_matter(
                raw_markdown,
                path.name,
            )
        )

        (
            curriculum_id,
            course,
            level,
            sequence,
            estimated_minutes,
        ) = self._validate_metadata(
            metadata,
            path.name,
        )

        fallback_title = (
            path.stem
            .replace("_", " ")
            .title()
        )

        title = self._extract_title(
            markdown_body,
            fallback_title,
        )

        content = self._clean_content(
            markdown_body
        )

        if not content:
            raise LearningContentMetadataError(
                f"Learning content file contains no lesson body: "
                f"{path.name}"
            )

        return LearningLessonDetail(
            id=path.stem,
            curriculum_id=curriculum_id,
            title=title,
            course=course,
            level=level,
            sequence=sequence,
            estimated_minutes=estimated_minutes,
            topic=self._topic_for_course(
                course
            ),
            description=self._build_description(
                content
            ),
            content=content,
        )

    def list_lessons(
        self,
    ) -> list[LearningLessonSummary]:
        """
        Return governed learner lessons in curriculum order.

        Python lessons are presented first, followed by
        Artificial Intelligence lessons.
        """
        lessons = [
            self._read_lesson(path)
            for path in self._lesson_files()
        ]

        course_order = {
            "Python": 0,
            "Artificial Intelligence": 1,
        }

        lessons.sort(
            key=lambda lesson: (
                course_order.get(
                    lesson.course,
                    99,
                ),
                lesson.sequence,
                lesson.id,
            )
        )

        return [
            LearningLessonSummary(
                id=lesson.id,
                curriculum_id=lesson.curriculum_id,
                title=lesson.title,
                course=lesson.course,
                level=lesson.level,
                sequence=lesson.sequence,
                estimated_minutes=(
                    lesson.estimated_minutes
                ),
                topic=lesson.topic,
                description=lesson.description,
            )
            for lesson in lessons
        ]

    def get_lesson(
        self,
        lesson_id: str,
    ) -> LearningLessonDetail:
        """
        Return one governed lesson by its stable API resource identifier.
        """
        safe_lesson_id = (
            lesson_id
            .strip()
            .lower()
        )

        if not re.fullmatch(
            r"lesson_[0-9]{2,4}",
            safe_lesson_id,
        ):
            raise LearningContentNotFoundError(
                lesson_id
            )

        path = (
            self.content_root
            / f"{safe_lesson_id}.md"
        )

        if not path.is_file():
            raise LearningContentNotFoundError(
                lesson_id
            )

        return self._read_lesson(
            path
        )