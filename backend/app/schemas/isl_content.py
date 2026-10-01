from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ISLAssetStatus = Literal[
    "available",
    "pending_review",
    "unavailable",
]


class ISLLessonSegment(BaseModel):
    segment_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    heading: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    source_text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    status: ISLAssetStatus

    asset_type: str | None = Field(
        default=None,
        max_length=50,
    )

    asset_path: str | None = Field(
        default=None,
        max_length=500,
    )

    caption: str | None = Field(
        default=None,
        max_length=5000,
    )

    validation_note: str | None = Field(
        default=None,
        max_length=1000,
    )


class ISLLessonManifest(BaseModel):
    lesson_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    curriculum_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    status: ISLAssetStatus

    segments: list[ISLLessonSegment]

    available_segments: int = Field(
        ...,
        ge=0,
    )

    total_segments: int = Field(
        ...,
        ge=0,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )
