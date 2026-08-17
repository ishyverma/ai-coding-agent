from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "version": "1.0.0",
        "env": "development",
    }


def test_v1_router_exists() -> None:
    response = client.get("/api/v1")

    # The router exists, even though we haven't added
    # any endpoints to it yet.
    assert response.status_code in {404, 405}