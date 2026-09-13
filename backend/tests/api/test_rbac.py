from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.rbac import require_teacher


def make_user(
    *,
    role="student",
    is_active=True,
):
    return SimpleNamespace(
        role=role,
        is_active=is_active,
    )


def test_teacher_is_allowed():
    teacher = make_user(role="teacher")

    result = require_teacher(current_user=teacher)

    assert result is teacher


@pytest.mark.parametrize(
    "role",
    [
        "student",
        "admin",
        "",
        None,
    ],
)
def test_non_teacher_roles_are_forbidden(role):
    user = make_user(role=role)

    with pytest.raises(HTTPException) as exc_info:
        require_teacher(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Teacher access required."


def test_inactive_teacher_is_forbidden():
    teacher = make_user(
        role="teacher",
        is_active=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_teacher(current_user=teacher)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User account is inactive."


@pytest.mark.parametrize(
    "role",
    [
        "TEACHER",
        "teacher",
        " Teacher ",
    ],
)
def test_teacher_role_is_normalized(role):
    teacher = make_user(role=role)

    result = require_teacher(current_user=teacher)

    assert result is teacher
