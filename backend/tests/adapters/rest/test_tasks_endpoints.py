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


def test_list_tasks_of_project_applies_status_filter(client: TestClient) -> None:
    """Regresión: esta ruta ignoraba en silencio `status`/`due_before`/`q`."""
    project = _create_project(client)
    todo = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Pendiente"}
    ).json()
    done = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Hecha"}
    ).json()
    client.post(f"/tasks/{done['id']}/complete")

    response = client.get(f"/projects/{project['id']}/tasks?status=todo")

    assert [t["id"] for t in response.json()] == [todo["id"]]


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


def test_get_task_returns_it(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == task["id"]


def test_get_missing_task_returns_404(client: TestClient) -> None:
    response = client.get(f"/tasks/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_update_task_description_explicit_null_clears_it(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Task", "description": "original"},
    ).json()

    response = client.patch(f"/tasks/{task['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_start_and_reopen_task(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    assert client.post(f"/tasks/{task['id']}/start").json()["status"] == "doing"
    assert client.post(f"/tasks/{task['id']}/reopen").json()["status"] == "todo"


def test_move_task_to_another_project(client: TestClient) -> None:
    origin = _create_project(client, "Origin")
    destination = _create_project(client, "Destination")
    task = client.post(
        f"/projects/{origin['id']}/tasks", json={"title": "Task"}
    ).json()

    response = client.post(
        f"/tasks/{task['id']}/move", json={"project_id": destination["id"]}
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == destination["id"]


def test_move_task_to_missing_project_returns_404(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    response = client.post(
        f"/tasks/{task['id']}/move", json={"project_id": str(uuid4())}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_delete_and_restore_task(client: TestClient) -> None:
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()

    delete_response = client.delete(f"/tasks/{task['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404

    restore_response = client.post(f"/tasks/{task['id']}/restore")
    assert restore_response.status_code == 200
    assert client.get(f"/tasks/{task['id']}").status_code == 200


def test_list_tasks_across_projects_with_filters(client: TestClient) -> None:
    project_a = _create_project(client, "A")
    project_b = _create_project(client, "B")
    task_a = client.post(
        f"/projects/{project_a['id']}/tasks",
        json={"title": "Pagar expensas", "due_date": "2026-07-01"},
    ).json()
    client.post(
        f"/projects/{project_b['id']}/tasks",
        json={"title": "Otra cosa", "due_date": "2026-12-01"},
    )

    response = client.get("/tasks?due_before=2026-07-28")

    assert [t["id"] for t in response.json()] == [task_a["id"]]

    response = client.get("/tasks?q=EXPENSAS")
    assert [t["id"] for t in response.json()] == [task_a["id"]]

    response = client.get(f"/tasks?project_id={project_b['id']}")
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Otra cosa"


def test_restore_task_under_deleted_project_returns_404(client: TestClient) -> None:
    """Regresión: borrar la única tarea de un proyecto lo deja vacío y por lo
    tanto borrable; restaurar la tarea después no debe reflotarla colgada de
    un proyecto invisible."""
    project = _create_project(client)
    task = client.post(
        f"/projects/{project['id']}/tasks", json={"title": "Task"}
    ).json()
    client.delete(f"/tasks/{task['id']}")
    delete_project_response = client.delete(f"/projects/{project['id']}")
    assert delete_project_response.status_code == 204

    response = client.post(f"/tasks/{task['id']}/restore")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
    assert client.get(f"/tasks/{task['id']}").status_code == 404
