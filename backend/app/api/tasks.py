import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import (
    RunResponse,
    RunTriggerResponse,
    TaskCreate,
    TaskResponse,
)


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Create a new coding task. Status starts as 'pending'."""

    created_task = crud.create_task(
        db=db,
        task_data=task,
    )

    logger.info(f"Task created: id={created_task.id}")

    return TaskResponse.model_validate(created_task)


@router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[TaskResponse]:
    """List all tasks, newest first."""

    tasks = crud.list_tasks(db, skip=skip, limit=limit)

    return [TaskResponse.model_validate(task) for task in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Get one task by ID. Returns 404 if not found."""

    task = crud.get_task(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return TaskResponse.model_validate(task)


@router.get(
    "/{task_id}/runs",
    response_model=list[RunResponse],
)
def list_task_runs(
    task_id: int,
    db: Session = Depends(get_db),
) -> list[RunResponse]:
    """List all runs for a task, newest first."""

    task = crud.get_task(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    runs = crud.list_runs_for_task(db, task_id)

    return [RunResponse.model_validate(run) for run in runs]


@router.post(
    "/{task_id}/run",
    response_model=RunTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_run(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RunTriggerResponse:
    """
    Trigger the agent to run on this task.

    Returns 202 Accepted immediately — the agent runs in the
    background. The client can then poll GET /runs/{run_id}
    or connect to the WebSocket /runs/{run_id}/stream for
    live logs.
    """

    task = crud.get_task(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Task is already running. Wait for it to " "finish before re-running."
            ),
        )

    run = crud.create_run(db, task_id=task_id)
    crud.update_task_status(db, task, "running")

    from app.services.runs import execute_run

    background_tasks.add_task(
        execute_run,
        task_id=task_id,
        run_id=run.id,
        repo_url=task.repo_url,
        task_text=task.task_text,
    )

    logger.info(f"Run triggered: run_id={run.id}, task_id={task_id}")

    return RunTriggerResponse(run_id=run.id)
