"""Test end-to-end del endpoint /health.

Primer test que ejercita el scaffolding de FastAPI de punta a punta.
"""

from fastapi.testclient import TestClient

from lifeos.adapters.rest.main import app

client = TestClient(app)


def test_health_ok() -> None:
    """GET /health responde 200 con {"status": "ok"}."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
