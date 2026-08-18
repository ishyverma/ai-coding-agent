from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """Data required to create a new coding task."""

    repo_url: str
    task_text: str


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
    created_at: datetime


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