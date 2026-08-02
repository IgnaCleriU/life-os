"""Tests de los endpoints REST de Project."""

from __future__ import annotations

from uuid import uuid4

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


def test_get_project_returns_it(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Life OS"}).json()

    response = client.get(f"/projects/{project['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


def test_get_missing_project_returns_404(client: TestClient) -> None:
    response = client.get(f"/projects/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_update_project_partial_fields(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Original"}).json()

    response = client.patch(f"/projects/{project['id']}", json={"name": "Renamed"})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_update_project_description_omitted_leaves_unchanged(
    client: TestClient,
) -> None:
    project = client.post(
        "/projects", json={"name": "Life OS", "description": "original"}
    ).json()

    response = client.patch(f"/projects/{project['id']}", json={"name": "Life OS v2"})

    assert response.json()["description"] == "original"


def test_update_project_description_explicit_null_clears_it(
    client: TestClient,
) -> None:
    project = client.post(
        "/projects", json={"name": "Life OS", "description": "original"}
    ).json()

    response = client.patch(
        f"/projects/{project['id']}", json={"description": None}
    )

    assert response.json()["description"] is None


def test_complete_archive_activate_project(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Life OS"}).json()

    assert (
        client.post(f"/projects/{project['id']}/complete").json()["status"]
        == "completed"
    )
    assert (
        client.post(f"/projects/{project['id']}/archive").json()["status"]
        == "archived"
    )
    assert (
        client.post(f"/projects/{project['id']}/activate").json()["status"]
        == "active"
    )


def test_reorder_up_and_down_swap_with_the_neighbor(client: TestClient) -> None:
    first = client.post("/projects", json={"name": "First"}).json()
    second = client.post("/projects", json={"name": "Second"}).json()
    assert (first["position"], second["position"]) == (0, 1)

    up = client.post(f"/projects/{second['id']}/reorder-up")
    assert up.status_code == 200
    assert up.json()["position"] == 0

    response = client.get("/projects")
    assert [p["id"] for p in response.json()] == [second["id"], first["id"]]

    down = client.post(f"/projects/{second['id']}/reorder-down")
    assert down.status_code == 200
    assert down.json()["position"] == 1


def test_reorder_up_on_the_first_project_is_a_noop(client: TestClient) -> None:
    first = client.post("/projects", json={"name": "First"}).json()
    client.post("/projects", json={"name": "Second"})

    response = client.post(f"/projects/{first['id']}/reorder-up")

    assert response.status_code == 200
    assert response.json()["position"] == 0


def test_reorder_missing_project_returns_404(client: TestClient) -> None:
    response = client.post(f"/projects/{uuid4()}/reorder-up")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_list_projects_filters_by_status(client: TestClient) -> None:
    client.post("/projects", json={"name": "Active"})
    archived = client.post("/projects", json={"name": "Archived"}).json()
    client.post(f"/projects/{archived['id']}/archive")

    response = client.get("/projects?status=archived")

    assert [p["id"] for p in response.json()] == [archived["id"]]


def test_list_projects_filters_by_text(client: TestClient) -> None:
    casa = client.post("/projects", json={"name": "Casa de campo"}).json()
    client.post("/projects", json={"name": "Finanzas"})

    response = client.get("/projects?q=CASA")

    assert [p["id"] for p in response.json()] == [casa["id"]]


def test_delete_empty_project_returns_204_and_hides_it(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Vacio"}).json()

    response = client.delete(f"/projects/{project['id']}")

    assert response.status_code == 204
    assert client.get(f"/projects/{project['id']}").status_code == 404


def test_delete_project_with_live_tasks_returns_409(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Con tareas"}).json()
    client.post(f"/projects/{project['id']}/tasks", json={"title": "Tarea"})

    response = client.delete(f"/projects/{project['id']}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "project_not_empty"


def test_restore_project_makes_it_visible_again(client: TestClient) -> None:
    project = client.post("/projects", json={"name": "Vacio"}).json()
    client.delete(f"/projects/{project['id']}")

    response = client.post(f"/projects/{project['id']}/restore")

    assert response.status_code == 200
    assert client.get(f"/projects/{project['id']}").status_code == 200
