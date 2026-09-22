"""Tests de la guardia local de la API REST (token + host, ADR 0009).

El escenario que se protege: la API escucha en loopback, pero cualquier
proceso local o página del navegador puede apuntarle. Sin el token correcto,
o con un `Host` que no sea loopback, nada pasa.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lifeos.infrastructure.config import get_settings

from .conftest import make_client

TOKEN = "s3cret-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def guarded(engine):
    with make_client(engine, api_token=TOKEN, auth_enabled=True) as client:
        yield client


def _error_code(response) -> str:
    return response.json()["error"]["code"]


def test_request_with_the_token_passes(guarded: TestClient) -> None:
    response = guarded.get("/projects", headers=AUTH)

    assert response.status_code == 200


def test_missing_token_is_401(guarded: TestClient) -> None:
    response = guarded.get("/projects")

    assert response.status_code == 401
    assert _error_code(response) == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_token_is_401(guarded: TestClient) -> None:
    response = guarded.get("/projects", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


def test_non_bearer_scheme_is_401(guarded: TestClient) -> None:
    response = guarded.get("/projects", headers={"Authorization": f"Basic {TOKEN}"})

    assert response.status_code == 401


def test_writes_are_blocked_without_the_token(guarded: TestClient) -> None:
    response = guarded.post("/projects", json={"name": "Casa"})

    assert response.status_code == 401
    assert guarded.get("/projects", headers=AUTH).json() == []


@pytest.mark.parametrize(
    "host", ["localhost:8000", "127.0.0.1:8000", "[::1]:8000", "localhost"]
)
def test_loopback_hosts_are_accepted(guarded: TestClient, host: str) -> None:
    response = guarded.get("/projects", headers={**AUTH, "Host": host})

    assert response.status_code == 200


@pytest.mark.parametrize("host", ["evil.example:8000", "192.168.1.10:8000", ""])
def test_other_hosts_are_403_even_with_the_token(
    guarded: TestClient, host: str
) -> None:
    """DNS rebinding: un dominio ajeno que resuelve a 127.0.0.1."""
    response = guarded.get("/projects", headers={**AUTH, "Host": host})

    assert response.status_code == 403
    assert _error_code(response) == "forbidden_host"


def test_cors_preflight_is_rejected_without_cors_headers(guarded: TestClient) -> None:
    response = guarded.options(
        "/projects",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers


def test_health_stays_open(guarded: TestClient) -> None:
    response = guarded.get("/health")

    assert response.status_code == 200


def test_auth_enabled_without_a_token_fails_closed(engine) -> None:
    with make_client(engine, api_token=None, auth_enabled=True) as client:
        response = client.get("/projects", headers=AUTH)

    assert response.status_code == 401
    assert "lifeos-daemon" in response.json()["error"]["message"]


class TestSettings:
    @pytest.fixture(autouse=True)
    def _fresh_settings(self):
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def test_auth_is_on_by_default(self, engine, monkeypatch) -> None:
        monkeypatch.delenv("LIFEOS_API_AUTH", raising=False)
        monkeypatch.delenv("LIFEOS_API_TOKEN", raising=False)

        with make_client(engine) as client:
            assert client.get("/projects").status_code == 401

    def test_token_from_the_environment(self, engine, monkeypatch) -> None:
        monkeypatch.delenv("LIFEOS_API_AUTH", raising=False)
        monkeypatch.setenv("LIFEOS_API_TOKEN", TOKEN)

        with make_client(engine) as client:
            assert client.get("/projects", headers=AUTH).status_code == 200

    def test_auth_can_be_disabled_explicitly(self, engine, monkeypatch) -> None:
        monkeypatch.setenv("LIFEOS_API_AUTH", "disabled")

        with make_client(engine) as client:
            assert client.get("/projects").status_code == 200
