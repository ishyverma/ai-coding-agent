from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_background_execution() -> None:
    """Prevent the trigger endpoint from actually running the agent."""

    with patch("app.services.runs.execute_run"):
        yield


def test_create_task() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["repo_url"] == ("https://github.com/example/test.git")

    assert data["task_text"] == ("Fix the failing tests")

    assert data["status"] == "pending"

    assert "id" in data


def test_create_task_empty_task_text() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "   ",
        },
    )

    assert response.status_code == 422


def test_list_tasks() -> None:
    response = client.get("/api/v1/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_task_not_found() -> None:
    response = client.get("/api/v1/tasks/99999")

    assert response.status_code == 404


def test_trigger_run_not_found() -> None:
    response = client.post("/api/v1/tasks/99999/run")

    assert response.status_code == 404


def test_list_task_runs() -> None:
    created = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    task_id = created.json()["id"]

    triggered = client.post(f"/api/v1/tasks/{task_id}/run")

    assert triggered.status_code == 202

    response = client.get(f"/api/v1/tasks/{task_id}/runs")

    assert response.status_code == 200

    runs = response.json()

    assert len(runs) == 1
    assert runs[0]["task_id"] == task_id
    assert runs[0]["status"] == "running"


def test_list_task_runs_not_found() -> None:
    response = client.get("/api/v1/tasks/99999/runs")

    assert response.status_code == 404


def test_trigger_run_starts_agent() -> None:
    created = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    task_id = created.json()["id"]

    response = client.post(f"/api/v1/tasks/{task_id}/run")

    assert response.status_code == 202

    data = response.json()

    assert "run_id" in data
    assert data["status"] == "started"


def test_trigger_run_conflict_while_running() -> None:
    created = client.post(
        "/api/v1/tasks",
        json={
            "repo_url": "https://github.com/example/test.git",
            "task_text": "Fix the failing tests",
        },
    )

    task_id = created.json()["id"]

    first = client.post(f"/api/v1/tasks/{task_id}/run")
    assert first.status_code == 202

    second = client.post(f"/api/v1/tasks/{task_id}/run")
    assert second.status_code == 409
