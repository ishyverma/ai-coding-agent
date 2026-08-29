from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_background_evals() -> None:
    """Prevent the eval trigger from actually running the eval suite."""

    with patch("app.api.evals._run_evals_in_background"):
        yield


def test_list_evals() -> None:
    response = client.get("/api/v1/evals")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trigger_eval_run() -> None:
    response = client.post("/api/v1/evals/run")

    assert response.status_code == 202
    assert "message" in response.json()
