from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    EvalResultResponse,
    RunLogResponse,
    RunResponse,
    TaskCreate,
    TaskResponse,
)


def test_task_create_schema() -> None:
    task = TaskCreate(
        repo_url="https://github.com/example/repo",
        task_text="Fix the failing tests",
    )

    assert task.repo_url == "https://github.com/example/repo"
    assert task.task_text == "Fix the failing tests"


def test_task_create_requires_repo_url() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(
            task_text="Fix the failing tests",
        )


def test_task_response_schema() -> None:
    task = TaskResponse(
        id=1,
        repo_url="https://github.com/example/repo",
        task_text="Fix the failing tests",
        status="pending",
        created_at=datetime.now(),
    )

    assert task.id == 1
    assert task.status == "pending"


def test_run_response_schema() -> None:
    run = RunResponse(
        id=1,
        task_id=1,
        status="running",
        attempts=1,
        tokens_used=500,
        duration_s=None,
        error_msg=None,
        created_at=datetime.now(),
        completed_at=None,
    )

    assert run.task_id == 1
    assert run.status == "running"


def test_run_log_response_schema() -> None:
    log = RunLogResponse(
        id=1,
        run_id=1,
        step="setup",
        level="info",
        message="Repository cloned",
        created_at=datetime.now(),
    )

    assert log.step == "setup"


def test_eval_result_response_schema() -> None:
    result = EvalResultResponse(
        id=1,
        eval_name="smoke_test",
        total_tasks=5,
        passed=4,
        failed=1,
        pass_rate=0.8,
        avg_attempts=1.5,
        avg_tokens=3000,
        avg_duration_s=12.5,
        run_at=datetime.now(),
    )

    assert result.pass_rate == 0.8
