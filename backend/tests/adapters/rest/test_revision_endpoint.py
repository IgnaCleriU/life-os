"""Tests de `GET /revision`."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _revision(client: TestClient) -> str:
    response = client.get("/revision")
    assert response.status_code == 200
    return response.json()["revision"]


def test_is_stable_while_nothing_is_written(client: TestClient) -> None:
    assert _revision(client) == _revision(client)


def test_reads_do_not_change_it(client: TestClient) -> None:
    before = _revision(client)

    client.get("/projects")
    client.get("/tasks")

    assert _revision(client) == before


def test_changes_after_a_write(client: TestClient) -> None:
    before = _revision(client)

    client.post("/projects", json={"name": "Casa"})

    assert _revision(client) != before
