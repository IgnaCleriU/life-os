"""Tests de `lifeos task ...`.

Sigue el estilo de `test_project_commands.py`: DB en memoria vía
`runner`/`db_session`, sin mockear casos de uso (wiring real). Cada grupo de
comandos cubre el camino feliz en texto plano y `--json`, más el error de
dominio relevante.
"""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from typer.testing import CliRunner

from lifeos.adapters.cli.main import app

# --- helpers ---------------------------------------------------------------


def _create_project(runner: CliRunner, name: str = "Groceries") -> str:
    result = runner.invoke(app, ["--json", "project", "create", name])
    return json.loads(result.stdout)["id"]


def _create_task(
    runner: CliRunner, project_id: str | None = None, title: str = "Buy milk"
) -> str:
    if project_id is None:
        project_id = _create_project(runner)
    result = runner.invoke(app, ["--json", "task", "create", project_id, title])
    return json.loads(result.stdout)["id"]


def _seed_doing_task(db_session, project_id: UUID, title: str) -> None:
    """Crea una tarea en curso directo por repositorio, sin pasar por el
    comando `start` (todavía no implementado en este grupo)."""
    from lifeos.domain import Task
    from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
        SQLiteTaskRepository,
    )

    repo = SQLiteTaskRepository(db_session)
    task = Task.create(project_id=project_id, title=title)
    task.start()
    repo.add(task)


# --- create ------------------------------------------------------------


def test_create_plain_prints_formatted_task(runner: CliRunner) -> None:
    project_id = _create_project(runner)

    result = runner.invoke(app, ["task", "create", project_id, "Buy milk"])
    assert result.exit_code == 0
    assert "Buy milk" in result.stdout
    assert "todo" in result.stdout
    assert result.stderr == ""


def test_create_with_all_options(runner: CliRunner) -> None:
    project_id = _create_project(runner)

    result = runner.invoke(
        app,
        [
            "--json",
            "task",
            "create",
            project_id,
            "Buy milk",
            "--priority",
            "high",
            "--due",
            "2026-08-01",
            "--description",
            "2%",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["priority"] == "high"
    assert payload["due_date"] == "2026-08-01"
    assert payload["description"] == "2%"


def test_create_json_prints_task_dict(runner: CliRunner) -> None:
    project_id = _create_project(runner)

    result = runner.invoke(app, ["--json", "task", "create", project_id, "Buy milk"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["title"] == "Buy milk"
    assert payload["status"] == "todo"
    assert payload["priority"] == "medium"
    assert payload["project_id"] == project_id
    assert "id" in payload


def test_create_bad_due_date_exits_2(runner: CliRunner) -> None:
    project_id = _create_project(runner)

    result = runner.invoke(
        app, ["task", "create", project_id, "Buy milk", "--due", "not-a-date"]
    )
    assert result.exit_code == 2
    assert result.stdout == ""


def test_create_project_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["task", "create", str(uuid4()), "Buy milk"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


def test_create_domain_validation_error_exits_1(runner: CliRunner) -> None:
    project_id = _create_project(runner)

    result = runner.invoke(app, ["task", "create", project_id, ""])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("domain_validation_error: ")


# --- list ----------------------------------------------------------------


def test_list_plain_prints_one_line_per_task(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    runner.invoke(app, ["task", "create", project_id, "Buy milk"])
    runner.invoke(app, ["task", "create", project_id, "Buy eggs"])

    result = runner.invoke(app, ["task", "list"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    assert "Buy milk" in result.stdout
    assert "Buy eggs" in result.stdout


def test_list_json_prints_list_of_task_dicts(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    runner.invoke(app, ["task", "create", project_id, "Buy milk"])

    result = runner.invoke(app, ["--json", "task", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert payload[0]["title"] == "Buy milk"


def test_list_filters_by_project(runner: CliRunner) -> None:
    project_a = _create_project(runner, "Groceries")
    project_b = _create_project(runner, "Chores")
    runner.invoke(app, ["task", "create", project_a, "Buy milk"])
    runner.invoke(app, ["task", "create", project_b, "Vacuum"])

    result = runner.invoke(app, ["--json", "task", "list", "--project", project_a])
    payload = json.loads(result.stdout)
    assert [t["title"] for t in payload] == ["Buy milk"]


def test_list_without_project_returns_all_projects(runner: CliRunner) -> None:
    project_a = _create_project(runner, "Groceries")
    project_b = _create_project(runner, "Chores")
    runner.invoke(app, ["task", "create", project_a, "Buy milk"])
    runner.invoke(app, ["task", "create", project_b, "Vacuum"])

    result = runner.invoke(app, ["--json", "task", "list"])
    payload = json.loads(result.stdout)
    assert {t["title"] for t in payload} == {"Buy milk", "Vacuum"}


def test_list_filters_by_status(runner: CliRunner, db_session) -> None:
    project_id = _create_project(runner)
    runner.invoke(app, ["task", "create", project_id, "Buy milk"])
    _seed_doing_task(db_session, UUID(project_id), "Vacuum")

    result = runner.invoke(app, ["--json", "task", "list", "--status", "doing"])
    payload = json.loads(result.stdout)
    assert [t["title"] for t in payload] == ["Vacuum"]


def test_list_filters_by_multiple_statuses(runner: CliRunner, db_session) -> None:
    project_id = _create_project(runner)
    runner.invoke(app, ["task", "create", project_id, "Buy milk"])
    _seed_doing_task(db_session, UUID(project_id), "Vacuum")

    result = runner.invoke(
        app,
        [
            "--json",
            "task",
            "list",
            "--status",
            "todo",
            "--status",
            "doing",
        ],
    )
    payload = json.loads(result.stdout)
    assert {t["title"] for t in payload} == {"Buy milk", "Vacuum"}


def test_list_filters_by_due_before(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    runner.invoke(
        app,
        ["task", "create", project_id, "Buy milk", "--due", "2026-08-01"],
    )
    runner.invoke(
        app,
        ["task", "create", project_id, "Buy eggs", "--due", "2026-09-01"],
    )

    result = runner.invoke(
        app, ["--json", "task", "list", "--due-before", "2026-08-15"]
    )
    payload = json.loads(result.stdout)
    assert [t["title"] for t in payload] == ["Buy milk"]


def test_list_filters_by_text(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    runner.invoke(app, ["task", "create", project_id, "Buy milk"])
    runner.invoke(app, ["task", "create", project_id, "Vacuum"])

    result = runner.invoke(app, ["--json", "task", "list", "--text", "milk"])
    payload = json.loads(result.stdout)
    assert [t["title"] for t in payload] == ["Buy milk"]


def test_list_empty_prints_nothing(runner: CliRunner) -> None:
    result = runner.invoke(app, ["task", "list"])
    assert result.exit_code == 0
    assert result.stdout == ""


# --- show ------------------------------------------------------------------


def test_show_plain_prints_formatted_task(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    task_id = _create_task(runner, project_id, "Buy milk")

    result = runner.invoke(app, ["task", "show", task_id])
    assert result.exit_code == 0
    assert "Buy milk" in result.stdout


def test_show_json_prints_task_dict(runner: CliRunner) -> None:
    project_id = _create_project(runner)
    task_id = _create_task(runner, project_id, "Buy milk")

    result = runner.invoke(app, ["--json", "task", "show", task_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == task_id
    assert payload["title"] == "Buy milk"


def test_show_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["task", "show", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("task_not_found: ")


def test_show_bad_uuid_exits_2(runner: CliRunner) -> None:
    result = runner.invoke(app, ["task", "show", "not-a-uuid"])
    assert result.exit_code == 2
    assert result.stdout == ""
