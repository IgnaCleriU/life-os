"""Tests de los endpoints REST de Project."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_project_returns_201_and_body(client: TestClient) -> None:
    response = client.post("/projects", json={"name": "Life OS"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Life OS"
    assert body["description"] is None
    assert body["status"] == "active"
    assert "id" in body
    assert "created_at" in body


def test_create_project_with_blank_name_returns_400(client: TestClient) -> None:
    response = client.post("/projects", json={"name": "   "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "domain_validation_error"


def test_create_project_missing_name_returns_422(client: TestClient) -> None:
    response = client.post("/projects", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


def test_list_projects_returns_created_projects(client: TestClient) -> None:
    first = client.post("/projects", json={"name": "First"}).json()
    second = client.post("/projects", json={"name": "Second"}).json()

    response = client.get("/projects")

    assert response.status_code == 200
    ids = {project["id"] for project in response.json()}
    assert ids == {first["id"], second["id"]}


def test_list_projects_empty_returns_empty_list(client: TestClient) -> None:
    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == []
