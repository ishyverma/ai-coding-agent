from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.schemas import TaskCreate


def create_task(db: Session, task_data: TaskCreate) -> models.Task:
    """Create a new coding task."""

    task = models.Task(
        repo_url=task_data.repo_url,
        task_text=task_data.task_text,
        status="pending",
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def get_task(db: Session, task_id: int) -> models.Task | None:
    """Get one task by its ID."""

    statement = select(models.Task).where(models.Task.id == task_id)

    return db.scalar(statement)


def list_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Task]:
    """Return a list of tasks."""

    statement = (
        select(models.Task)
        .order_by(models.Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def create_run(
    db: Session,
    task_id: int,
) -> models.Run:
    """Create a new agent run for a task."""

    run = models.Run(
        task_id=task_id,
        status="running",
        attempts=0,
        tokens_used=0,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def get_run(
    db: Session,
    run_id: int,
) -> models.Run | None:
    """Get one run by its ID."""

    statement = select(models.Run).where(models.Run.id == run_id)

    return db.scalar(statement)


def list_runs_for_task(
    db: Session,
    task_id: int,
) -> list[models.Run]:
    """Return all runs belonging to a task."""

    statement = (
        select(models.Run)
        .where(models.Run.task_id == task_id)
        .order_by(models.Run.created_at.desc())
    )

    return list(db.scalars(statement).all())


def update_run(
    db: Session,
    run: models.Run,
    *,
    status: str | None = None,
    attempts: int | None = None,
    tokens_used: int | None = None,
    duration_s: float | None = None,
    error_msg: str | None = None,
    completed_at=None,
) -> models.Run:
    """Update fields on an existing run."""

    if status is not None:
        run.status = status

    if attempts is not None:
        run.attempts = attempts

    if tokens_used is not None:
        run.tokens_used = tokens_used

    if duration_s is not None:
        run.duration_s = duration_s

    if error_msg is not None:
        run.error_msg = error_msg

    if completed_at is not None:
        run.completed_at = completed_at

    db.commit()
    db.refresh(run)

    return run


def create_run_log(
    db: Session,
    run_id: int,
    step: str,
    message: str,
    level: str = "info",
    diff: str | None = None,
) -> models.RunLog:
    """Create one log entry for an agent run."""

    log = models.RunLog(
        run_id=run_id,
        step=step,
        level=level,
        message=message,
        diff=diff,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def get_run_logs(
    db: Session,
    run_id: int,
) -> list[models.RunLog]:
    """Return all logs for a run in chronological order."""

    statement = (
        select(models.RunLog)
        .where(models.RunLog.run_id == run_id)
        .order_by(models.RunLog.created_at.asc())
    )

    return list(db.scalars(statement).all())


def update_task_status(
    db: Session,
    task: models.Task,
    status: str,
) -> models.Task:
    """Update the status of a task."""

    task.status = status

    db.commit()
    db.refresh(task)

    return task


def mark_interrupted_runs_failed(db: Session) -> int:
    """
    Mark in-progress runs as failed after a server restart.

    BackgroundTasks are process-local. If the server stops while a run is
    active, that run cannot resume, so keeping it running blocks the task.
    """

    runs = list(db.scalars(select(models.Run).where(models.Run.status == "running")))

    for run in runs:
        run.status = "failed"
        run.error_msg = "Server restarted before this run completed."
        run.completed_at = datetime.utcnow()

        task = db.get(models.Task, run.task_id)

        if task is not None and task.status == "running":
            task.status = "failed"

    db.commit()

    return len(runs)


def create_eval_result(
    db: Session,
    eval_name: str,
    total: int,
    passed: int,
    failed: int,
    pass_rate: float,
    avg_attempts: float,
    avg_tokens: float,
    avg_duration_s: float,
) -> models.EvalResult:
    """Create one aggregate eval result."""

    result = models.EvalResult(
        eval_name=eval_name,
        total_tasks=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        avg_attempts=avg_attempts,
        avg_tokens=avg_tokens,
        avg_duration_s=avg_duration_s,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result


def list_eval_results(
    db: Session,
) -> list[models.EvalResult]:
    """Return all eval results, newest first."""

    statement = select(models.EvalResult).order_by(models.EvalResult.run_at.desc())

    return list(db.scalars(statement).all())
