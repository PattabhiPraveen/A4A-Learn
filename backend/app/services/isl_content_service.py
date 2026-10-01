from __future__ import annotations

import json
import re
from pathlib import Path

from app.schemas.isl_content import (
    ISLLessonManifest,
)


class ISLContentNotFoundError(Exception):
    """Raised when an ISL lesson manifest does not exist."""


class ISLContentValidationError(ValueError):
    """Raised when governed ISL content is invalid."""


class ISLContentService:
    """
    Reads governed ISL learning manifests.

    This service never generates or invents signs.

    Only explicitly registered and validated ISL assets may
    be returned as available learner-facing content.
    """

    def __init__(
        self,
        content_root: Path | None = None,
    ) -> None:
        project_root = (
            Path(__file__).resolve().parents[3]
        )

        self.content_root = (
            content_root
            if content_root is not None
            else project_root
            / "datasets"
            / "raw"
            / "DS003_ISL_Learning"
        )

        self.manifest_root = (
            self.content_root
            / "manifests"
        )

        self.asset_root = (
            self.content_root
            / "assets"
        )


    @staticmethod
    def _safe_lesson_id(
        lesson_id: str,
    ) -> str:
        normalized = (
            lesson_id
            .strip()
            .lower()
        )

        if not re.fullmatch(
            r"lesson_[0-9]{2,4}",
            normalized,
        ):
            raise ISLContentNotFoundError(
                lesson_id
            )

        return normalized


    def get_manifest(
        self,
        lesson_id: str,
    ) -> ISLLessonManifest:
        safe_lesson_id = (
            self._safe_lesson_id(
                lesson_id
            )
        )

        path = (
            self.manifest_root
            / f"{safe_lesson_id}.json"
        )

        if not path.is_file():
            raise ISLContentNotFoundError(
                lesson_id
            )

        try:
            raw = json.loads(
                path.read_text(
                    encoding="utf-8-sig",
                )
            )

            manifest = (
                ISLLessonManifest.model_validate(
                    {
                        **raw,
                        "available_segments": 0,
                        "total_segments": len(
                            raw.get(
                                "segments",
                                [],
                            )
                        ),
                        "message": (
                            "ISL learning content is "
                            "being prepared and validated."
                        ),
                    }
                )
            )

        except (
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ) as exc:
            raise ISLContentValidationError(
                f"Invalid ISL manifest: {path.name}"
            ) from exc

        if (
            manifest.lesson_id
            != safe_lesson_id
        ):
            raise ISLContentValidationError(
                "ISL manifest lesson_id does not "
                "match its resource filename."
            )

        available_count = 0

        for segment in manifest.segments:
            if segment.status != "available":
                continue

            if (
                not segment.asset_path
                or not segment.asset_type
            ):
                raise ISLContentValidationError(
                    "Available ISL segments must "
                    "declare asset_type and asset_path."
                )

            asset_path = (
                self.asset_root
                / segment.asset_path
            ).resolve()

            asset_root = (
                self.asset_root.resolve()
            )

            try:
                asset_path.relative_to(
                    asset_root
                )
            except ValueError as exc:
                raise ISLContentValidationError(
                    "ISL asset path escapes the "
                    "approved asset directory."
                ) from exc

            if not asset_path.is_file():
                raise ISLContentValidationError(
                    "Available ISL asset does "
                    "not exist."
                )

            available_count += 1

        if (
            available_count
            == len(manifest.segments)
            and available_count > 0
        ):
            overall_status = "available"
            message = (
                "Validated ISL learning content "
                "is available for this lesson."
            )

        elif available_count > 0:
            overall_status = "pending_review"
            message = (
                "Some validated ISL learning "
                "content is available. Remaining "
                "segments are under review."
            )

        else:
            overall_status = "pending_review"
            message = (
                "ISL learning content for this "
                "lesson is being prepared and "
                "validated. The written and visual "
                "lesson remains available."
            )

        return manifest.model_copy(
            update={
                "status": overall_status,
                "available_segments": (
                    available_count
                ),
                "total_segments": len(
                    manifest.segments
                ),
                "message": message,
            }
        )
