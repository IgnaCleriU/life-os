"""Tests de `POST /quick-add/preview` y `POST /quick-add`.

El parser y la resolución de proyecto tienen sus propios tests en
`tests/adapters/shared/`; acá se verifica el cableado HTTP: forma de las
respuestas, códigos de error, y que el preview nunca escriba.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def _project(client: TestClient, name: str) -> dict:
    return client.post("/projects", json={"name": name}).json()


def _preview(client: TestClient, text: str, **extra) -> dict:
    response = client.post("/quick-add/preview", json={"text": text, **extra})
    assert response.status_code == 200
    return response.json()


def _next_weekday(target: int) -> date:
    today = date.today()
    delta = (target - today.weekday()) % 7 or 7
    return today + timedelta(days=delta)


# --- preview -----------------------------------------------------------------


def test_preview_parses_every_token(client: TestClient) -> None:
    casa = _project(client, "Casa")

    body = _preview(client, "comprar filtros !high @sat #casa")

    assert body == {
        "title": "comprar filtros",
        "priority": "high",
        "due_date": _next_weekday(5).isoformat(),
        "project": {"id": casa["id"], "name": "Casa"},
        "error": None,
    }


def test_preview_uses_the_default_project(client: TestClient) -> None:
    casa = _project(client, "Casa")

    body = _preview(client, "limpiar canaletas", default_project_id=casa["id"])

    assert body["project"] == {"id": casa["id"], "name": "Casa"}


def test_preview_without_project_points_at_inbox_without_creating_it(
    client: TestClient,
) -> None:
    body = _preview(client, "algo")

    assert body["project"] == {"id": None, "name": "inbox"}
    assert client.get("/projects").json() == []


def test_preview_unknown_project_is_an_error(client: TestClient) -> None:
    body = _preview(client, "algo #nada")

    assert body["project"] is None
    assert body["error"]["code"] == "project_name_not_found"


def test_preview_ambiguous_project_is_an_error(client: TestClient) -> None:
    _project(client, "Casa")
    _project(client, "casa")

    body = _preview(client, "algo #casa")

    assert body["error"]["code"] == "ambiguous_project_name"


def test_preview_missing_default_project_is_an_error(client: TestClient) -> None:
    body = _preview(
        client, "algo", default_project_id="00000000-0000-0000-0000-000000000000"
    )

    assert body["error"]["code"] == "project_not_found"


def test_preview_empty_title_is_an_error(client: TestClient) -> None:
    _project(client, "Casa")

    body = _preview(client, "!high #casa")

    assert body["error"]["code"] == "domain_validation_error"


# --- create ------------------------------------------------------------------


def test_create_lands_in_the_named_project(client: TestClient) -> None:
    casa = _project(client, "Casa")

    response = client.post("/quick-add", json={"text": "llamar al gasista !high #casa"})

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "llamar al gasista"
    assert task["priority"] == "high"
    assert task["project_id"] == casa["id"]


def test_create_uses_the_default_project(client: TestClient) -> None:
    _project(client, "Casa")
    finanzas = _project(client, "Finanzas")

    response = client.post(
        "/quick-add", json={"text": "pagar", "default_project_id": finanzas["id"]}
    )

    assert response.json()["project_id"] == finanzas["id"]


def test_create_without_project_creates_the_inbox(client: TestClient) -> None:
    response = client.post("/quick-add", json={"text": "algo"})

    assert response.status_code == 201
    projects = client.get("/projects").json()
    assert [p["name"] for p in projects] == ["inbox"]
    assert response.json()["project_id"] == projects[0]["id"]


def test_create_unknown_project_is_404(client: TestClient) -> None:
    response = client.post("/quick-add", json={"text": "algo #nada"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_name_not_found"


def test_create_ambiguous_project_is_409(client: TestClient) -> None:
    _project(client, "Casa")
    _project(client, "casa")

    response = client.post("/quick-add", json={"text": "algo #casa"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ambiguous_project_name"
    assert client.get("/tasks").json() == []


def test_create_empty_title_is_400(client: TestClient) -> None:
    _project(client, "Casa")

    response = client.post("/quick-add", json={"text": "#casa"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "domain_validation_error"


def test_create_empty_title_does_not_create_the_inbox(client: TestClient) -> None:
    response = client.post("/quick-add", json={"text": "!high"})

    assert response.status_code == 400
    assert client.get("/projects").json() == []
