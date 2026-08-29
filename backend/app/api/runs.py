import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import RunLogResponse, RunResponse


router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)


@router.get(
    "/{run_id}",
    response_model=RunResponse,
)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> RunResponse:
    """Get a run's status, attempts, tokens used, and duration."""

    run = crud.get_run(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found",
        )

    return RunResponse.model_validate(run)


@router.get(
    "/{run_id}/logs",
    response_model=list[RunLogResponse],
)
def get_run_logs(
    run_id: int,
    db: Session = Depends(get_db),
) -> list[RunLogResponse]:
    """Get all log entries for a run, in chronological order."""

    run = crud.get_run(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found",
        )

    logs = crud.get_run_logs(db, run_id)

    return [RunLogResponse.model_validate(log) for log in logs]


@router.websocket(
    "/{run_id}/stream",
)
async def stream_run_logs(
    run_id: int,
    websocket: WebSocket,
) -> None:
    """
    WebSocket endpoint for real-time log streaming.

    The client connects here and receives log entries as JSON
    as they appear. The connection closes automatically when
    the run finishes.

    Message format:
        {"type": "log", "data": {RunLogResponse fields}}
        {"type": "done", "status": "passed" | "failed" | "gave_up"}
        {"type": "error", "message": "..."}
    """

    await websocket.accept()

    from app.database import SessionLocal

    last_seen_id = 0

    try:
        while True:
            db = SessionLocal()

            try:
                run = crud.get_run(db, run_id)

                if run is None:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Run not found",
                        }
                    )
                    break

                new_logs = crud.get_run_logs(db, run_id)

                for log in new_logs:
                    if log.id <= last_seen_id:
                        continue

                    await websocket.send_json(
                        {
                            "type": "log",
                            "data": RunLogResponse.model_validate(log).model_dump(
                                mode="json"
                            ),
                        }
                    )
                    last_seen_id = log.id

                if run.status in ("passed", "failed", "gave_up"):
                    await websocket.send_json(
                        {
                            "type": "done",
                            "status": run.status,
                        }
                    )
                    break

            finally:
                db.close()

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
