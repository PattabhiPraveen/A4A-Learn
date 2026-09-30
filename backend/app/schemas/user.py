from typing import Literal

from pydantic import BaseModel, EmailStr, Field  # type: ignore[import]


AccessibilityProfile = Literal[
    "standard",
    "deaf",
    "hard_of_hearing",
    "non_speaking",
]


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    accessibility_profile: AccessibilityProfile = "standard"
    preferred_language: str = "english"
    isl_enabled: bool = False
    captions_enabled: bool = False
    is_active: bool

    class Config:
        from_attributes = True


class AccessibilityProfileUpdate(BaseModel):
    accessibility_profile: AccessibilityProfile
    preferred_language: str = Field(
        default="english",
        min_length=2,
        max_length=30,
    )
    isl_enabled: bool = False
    captions_enabled: bool = False