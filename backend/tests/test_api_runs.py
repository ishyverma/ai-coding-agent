from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import crud
from app.database import SessionLocal
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_background_execution() -> None:
    """Prevent the trigger endpoint from actually running the agent."""

    with patch("app.services.runs.execute_run"):
        yield


def test_get_run_not_found() -> None:
    response = client.get("/api/v1/runs/99999")

    assert response.status_code == 404


def test_get_run_logs_not_found() -> None:
    response = client.get("/api/v1/runs/99999/logs")

    assert response.status_code == 404


def test_get_run_and_logs_after_task_created() -> None:
    created = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    task_id = created.json()["id"]

    triggered = client.post(f"/api/v1/tasks/{task_id}/run")
    run_id = triggered.json()["run_id"]

    response = client.get(f"/api/v1/runs/{run_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == run_id
    assert data["task_id"] == task_id
    assert data["status"] == "running"
    assert data["attempts"] == 0
    assert data["tokens_used"] == 0


def test_stream_websocket_sends_done_for_finished_run() -> None:
    created = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    task_id = created.json()["id"]

    triggered = client.post(f"/api/v1/tasks/{task_id}/run")
    run_id = triggered.json()["run_id"]

    db = SessionLocal()

    try:
        run = crud.get_run(db, run_id)
        crud.update_run(
            db,
            run,
            status="passed",
            attempts=1,
            completed_at=datetime.utcnow(),
        )
    finally:
        db.close()

    with client.websocket_connect(f"/api/v1/runs/{run_id}/stream") as websocket:
        message = websocket.receive_json()

        assert message["type"] == "done"
        assert message["status"] == "passed"
