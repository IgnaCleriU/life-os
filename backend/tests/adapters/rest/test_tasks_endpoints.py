"""Tests de los endpoints REST de Task."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def _create_project(client: TestClient, name: str = "Project") -> dict:
    return client.post("/projects", json={"name": name}).json()


def test_create_task_under_existing_project_returns_201(client: TestClient) -> None:
    project = _create_project(client)

    response = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Do something"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["status"] == "todo"
    assert body["priority"] == "medium"
    assert body["due_date"] is None


def test_create_task_under_missing_project_returns_404(client: TestClient) -> None:
    response = client.post(
        f"/projects/{uuid4()}/tasks", json={"title": "Do something"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_create_task_with_blank_title_returns_400(client: TestClient) -> None:
    project = _create_project(client)

    response = client.post(f"/projects/{project['id']}/tasks", json={"title": "  "})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "domain_validation_error"


def test_list_tasks_returns_only_that_projects_tasks(client: TestClient) -> None:
    project_a = _create_project(client, "A")
    project_b = _create_project(client, "B")
    task_a = client.post(
        f"/projects/{project_a['id']}/tasks", json={"title": "Task A"}
    ).json()
    client.post(f"/projects/{project_b['id']}/tasks", json={"title": "Task B"})

    response = client.get(f"/projects/{project_a['id']}/tasks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == task_a["id"]


def test_list_tasks_unknown_project_returns_empty_list(client: TestClient) -> None:
    response = client.get(f"/projects/{uuid4()}/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_update_task_partial_fields(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Original"}
    ).json()

    response = client.patch(f"/tasks/{task['id']}", json={"title": "Renamed"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["due_date"] is None


def test_update_task_due_date_omitted_leaves_unchanged(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Task", "due_date": "2026-01-01"},
    ).json()

    response = client.patch(f"/tasks/{task['id']}", json={"title": "Task renamed"})

    assert response.status_code == 200
    assert response.json()["due_date"] == "2026-01-01"


def test_update_task_due_date_explicit_null_clears_it(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Task", "due_date": "2026-01-01"},
    ).json()

    response = client.patch(f"/tasks/{task['id']}", json={"due_date": None})

    assert response.status_code == 200
    assert response.json()["due_date"] is None


def test_update_missing_task_returns_404(client: TestClient) -> None:
    response = client.patch(f"/tasks/{uuid4()}", json={"title": "New"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_complete_task_returns_done_status(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    response = client.post(f"/tasks/{task['id']}/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_complete_task_is_idempotent(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    first = client.post(f"/tasks/{task['id']}/complete")
    second = client.post(f"/tasks/{task['id']}/complete")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "done"


def test_complete_missing_task_returns_404(client: TestClient) -> None:
    response = client.post(f"/tasks/{uuid4()}/complete")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"
