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


def test_missing_path_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FileChange(
            content="print('hello')",
        )


def test_empty_file_content_is_allowed() -> None:
    """Empty content is allowed by the schema; it is filtered out later.

    Rejecting it at the tool-call level made Groq fail the whole request
    with a 400 instead of returning a plan we can clean up.
    """

    change = FileChange(
        path="calculator.py",
        content="",
    )

    assert change.path == "calculator.py"
    assert change.content == ""
