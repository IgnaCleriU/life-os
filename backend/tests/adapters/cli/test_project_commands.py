"""Tests de `lifeos project ...`.

Sigue el estilo de `test_skeleton.py`: DB en memoria vía `runner`/`cli_env`,
sin mockear casos de uso (wiring real). Cada grupo de comandos cubre el
camino feliz en texto plano y `--json`, más el error de dominio relevante.
"""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from typer.testing import CliRunner

from lifeos.adapters.cli.main import app

# --- create ------------------------------------------------------------


def test_create_plain_prints_formatted_project(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "create", "Groceries"])
    assert result.exit_code == 0
    assert "Groceries" in result.stdout
    assert "active" in result.stdout
    assert result.stderr == ""


def test_create_with_description(runner: CliRunner, db_session) -> None:
    result = runner.invoke(
        app, ["project", "create", "Groceries", "--description", "Weekly shop"]
    )
    assert result.exit_code == 0
    assert "Groceries" in result.stdout


def test_create_json_prints_project_dict(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--json", "project", "create", "Groceries"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "Groceries"
    assert payload["status"] == "active"
    assert "id" in payload


def test_create_domain_validation_error_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "create", ""])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("domain_validation_error: ")


# --- list ----------------------------------------------------------------


def test_list_plain_prints_one_line_per_project(runner: CliRunner) -> None:
    runner.invoke(app, ["project", "create", "Groceries"])
    runner.invoke(app, ["project", "create", "Chores"])

    result = runner.invoke(app, ["project", "list"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 2
    assert "Groceries" in result.stdout
    assert "Chores" in result.stdout


def test_list_json_prints_list_of_project_dicts(runner: CliRunner) -> None:
    runner.invoke(app, ["project", "create", "Groceries"])

    result = runner.invoke(app, ["--json", "project", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert payload[0]["name"] == "Groceries"


def _seed_archived_project(db_session, name: str) -> None:
    """Crea y archiva un proyecto directo por repositorio, sin pasar por el
    comando `archive` (todavía no implementado en este grupo)."""
    from lifeos.domain import Project
    from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
        SQLiteProjectRepository,
    )

    repo = SQLiteProjectRepository(db_session)
    project = Project.create(name)
    project.archive()
    repo.add(project)


def test_list_filters_by_status(runner: CliRunner, db_session) -> None:
    runner.invoke(app, ["project", "create", "Groceries"])
    _seed_archived_project(db_session, "Chores")

    result = runner.invoke(app, ["--json", "project", "list", "--status", "archived"])
    payload = json.loads(result.stdout)
    assert [p["name"] for p in payload] == ["Chores"]


def test_list_filters_by_multiple_statuses(runner: CliRunner, db_session) -> None:
    runner.invoke(app, ["project", "create", "Groceries"])
    _seed_archived_project(db_session, "Chores")

    result = runner.invoke(
        app,
        [
            "--json",
            "project",
            "list",
            "--status",
            "active",
            "--status",
            "archived",
        ],
    )
    payload = json.loads(result.stdout)
    assert {p["name"] for p in payload} == {"Groceries", "Chores"}


def test_list_filters_by_text(runner: CliRunner) -> None:
    runner.invoke(app, ["project", "create", "Groceries"])
    runner.invoke(app, ["project", "create", "Chores"])

    result = runner.invoke(app, ["--json", "project", "list", "--text", "Groc"])
    payload = json.loads(result.stdout)
    assert [p["name"] for p in payload] == ["Groceries"]


def test_list_empty_prints_nothing(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "list"])
    assert result.exit_code == 0
    assert result.stdout == ""


# --- show ------------------------------------------------------------------


def test_show_plain_prints_formatted_project(runner: CliRunner) -> None:
    create_result = runner.invoke(app, ["--json", "project", "create", "Groceries"])
    project_id = json.loads(create_result.stdout)["id"]

    result = runner.invoke(app, ["project", "show", project_id])
    assert result.exit_code == 0
    assert "Groceries" in result.stdout


def test_show_json_prints_project_dict(runner: CliRunner) -> None:
    create_result = runner.invoke(app, ["--json", "project", "create", "Groceries"])
    project_id = json.loads(create_result.stdout)["id"]

    result = runner.invoke(app, ["--json", "project", "show", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == project_id
    assert payload["name"] == "Groceries"


def test_show_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "show", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


def test_show_bad_uuid_exits_2(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "show", "not-a-uuid"])
    assert result.exit_code == 2
    assert result.stdout == ""


# --- update ------------------------------------------------------------


def _create(runner: CliRunner, name: str = "Groceries") -> str:
    result = runner.invoke(app, ["--json", "project", "create", name])
    return json.loads(result.stdout)["id"]


def test_update_name_plain(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "update", project_id, "--name", "Errands"])
    assert result.exit_code == 0
    assert "Errands" in result.stdout
    assert result.stderr == ""


def test_update_description_json(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(
        app,
        ["--json", "project", "update", project_id, "--description", "New desc"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["description"] == "New desc"
    assert payload["name"] == "Groceries"


def test_update_no_fields_leaves_project_untouched(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["--json", "project", "update", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "Groceries"
    assert payload["description"] is None


def test_update_clear_description(runner: CliRunner) -> None:
    project_id = _create(runner)
    runner.invoke(app, ["project", "update", project_id, "--description", "Something"])

    result = runner.invoke(
        app, ["--json", "project", "update", project_id, "--clear-description"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["description"] is None


def test_update_description_and_clear_description_mutually_exclusive(
    runner: CliRunner,
) -> None:
    project_id = _create(runner)

    result = runner.invoke(
        app,
        [
            "project",
            "update",
            project_id,
            "--description",
            "x",
            "--clear-description",
        ],
    )
    assert result.exit_code == 2
    assert result.stdout == ""


def test_update_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(
        app, ["project", "update", str(uuid4()), "--name", "Errands"]
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


# --- complete/archive/activate ------------------------------------------


def test_complete_plain(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "complete", project_id])
    assert result.exit_code == 0
    assert "completed" in result.stdout
    assert result.stderr == ""


def test_complete_json(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["--json", "project", "complete", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"


def test_complete_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "complete", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


def test_archive_plain(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "archive", project_id])
    assert result.exit_code == 0
    assert "archived" in result.stdout
    assert result.stderr == ""


def test_archive_json(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["--json", "project", "archive", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "archived"


def test_archive_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "archive", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


def test_activate_plain(runner: CliRunner) -> None:
    project_id = _create(runner)
    runner.invoke(app, ["project", "archive", project_id])

    result = runner.invoke(app, ["project", "activate", project_id])
    assert result.exit_code == 0
    assert "active" in result.stdout
    assert result.stderr == ""


def test_activate_json(runner: CliRunner) -> None:
    project_id = _create(runner)
    runner.invoke(app, ["project", "archive", project_id])

    result = runner.invoke(app, ["--json", "project", "activate", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "active"


def test_activate_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "activate", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


# --- delete/restore ------------------------------------------------------


def _seed_task(db_session, project_id) -> None:
    """Crea una tarea viva bajo el proyecto dado, directo por repositorio."""
    from lifeos.domain import Task
    from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
        SQLiteTaskRepository,
    )

    repo = SQLiteTaskRepository(db_session)
    task = Task.create(project_id=project_id, title="Buy milk")
    repo.add(task)


def test_delete_confirm_accepted(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "delete", project_id], input="y\n")
    assert result.exit_code == 0
    assert result.stderr == ""

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 1
    assert show_result.stderr.startswith("project_not_found: ")


def test_delete_confirm_declined(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "delete", project_id], input="n\n")
    assert result.exit_code == 1

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 0


def test_delete_yes_flag_skips_prompt(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "delete", project_id, "--yes"])
    assert result.exit_code == 0

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 1


def test_delete_short_yes_flag_skips_prompt(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "delete", project_id, "-y"])
    assert result.exit_code == 0

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 1


def test_delete_empty_input_aborts(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(app, ["project", "delete", project_id], input="")
    assert result.exit_code == 1

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 0


def test_delete_json_prints_deleted_project(runner: CliRunner) -> None:
    project_id = _create(runner)

    result = runner.invoke(
        app, ["--json", "project", "delete", project_id, "--yes"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == project_id


def test_delete_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "delete", str(uuid4()), "--yes"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")


def test_delete_project_not_empty_exits_1(runner: CliRunner, db_session) -> None:
    project_id = _create(runner)
    _seed_task(db_session, UUID(project_id))

    result = runner.invoke(app, ["project", "delete", project_id, "--yes"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_empty: ")


def test_restore_plain(runner: CliRunner) -> None:
    project_id = _create(runner)
    runner.invoke(app, ["project", "delete", project_id, "--yes"])

    result = runner.invoke(app, ["project", "restore", project_id])
    assert result.exit_code == 0
    assert result.stderr == ""

    show_result = runner.invoke(app, ["project", "show", project_id])
    assert show_result.exit_code == 0


def test_restore_json(runner: CliRunner) -> None:
    project_id = _create(runner)
    runner.invoke(app, ["project", "delete", project_id, "--yes"])

    result = runner.invoke(app, ["--json", "project", "restore", project_id])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == project_id


def test_restore_not_found_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["project", "restore", str(uuid4())])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_not_found: ")
