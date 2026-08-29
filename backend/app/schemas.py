from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TaskCreate(BaseModel):
    """Data required to create a new coding task."""

    repo_url: str
    task_text: str

    @field_validator("task_text")
    @classmethod
    def task_text_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task_text cannot be empty")
        return value.strip()

    @field_validator("repo_url")
    @classmethod
    def repo_url_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("repo_url cannot be empty")
        return value.strip()


class TaskResponse(BaseModel):
    """Data returned when exposing a task through the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    repo_url: str
    task_text: str
    status: str
    created_at: datetime


class RunResponse(BaseModel):
    """Data returned when exposing a run through the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    status: str
    attempts: int
    tokens_used: int
    duration_s: float | None
    error_msg: str | None
    created_at: datetime
    completed_at: datetime | None


class RunLogResponse(BaseModel):
    """Data returned for a run log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    step: str
    level: str
    message: str
    diff: str | None = None
    created_at: datetime


class RunTriggerResponse(BaseModel):
    """Response returned when a run is triggered on a task."""

    run_id: int
    status: str = "started"
    message: str = "Agent started. Connect to /runs/{run_id}/stream " "for live logs."


class EvalResultResponse(BaseModel):
    """Data returned for an evaluation result."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    eval_name: str
    total_tasks: int
    passed: int
    failed: int
    pass_rate: float
    avg_attempts: float
    avg_tokens: float
    avg_duration_s: float
    run_at: datetime
