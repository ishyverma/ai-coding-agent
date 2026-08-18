import pytest
from pydantic import ValidationError

from app.agent.schemas import (
    CodeChangePlan,
    FileChange,
)


def test_file_change_schema() -> None:
    change = FileChange(
        path="app.py",
        content="print('hello')",
    )

    assert change.path == "app.py"
    assert change.content == "print('hello')"


def test_code_change_plan_schema() -> None:
    plan = CodeChangePlan(
        changes=[
            FileChange(
                path="app.py",
                content="print('hello')",
            )
        ],
        test_command="pytest -q",
    )

    assert len(plan.changes) == 1
    assert plan.test_command == "pytest -q"


def test_code_change_plan_defaults() -> None:
    plan = CodeChangePlan()

    assert plan.changes == []
    assert plan.test_command == "pytest -q"


def test_invalid_file_change_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FileChange(
            path="app.py",
        )

def test_empty_file_content_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FileChange(
            path="calculator.py",
            content="",
        )