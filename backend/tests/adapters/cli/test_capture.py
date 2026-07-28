"""Tests de `lifeos capture ...` / `lifeos add ...`.

Sigue el estilo de `test_task_commands.py`: DB en memoria vía
`runner`/`db_session`, sin mockear casos de uso (wiring real). Cubre el
get-or-create del proyecto `inbox` por defecto, la resolución de `#nombre`
a proyecto existente, la integración con `parse_quick_add`, y la paridad
del alias `add`.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from lifeos.adapters.cli.main import app
from lifeos.domain import Project

# --- helpers ---------------------------------------------------------------


def _create_project(runner: CliRunner, name: str = "Groceries") -> str:
    result = runner.invoke(app, ["--json", "project", "create", name])
    return json.loads(result.stdout)["id"]


def _list_projects(runner: CliRunner) -> list[dict]:
    result = runner.invoke(app, ["--json", "project", "list"])
    return json.loads(result.stdout)


def _list_tasks(runner: CliRunner) -> list[dict]:
    result = runner.invoke(app, ["--json", "task", "list"])
    return json.loads(result.stdout)


# --- inbox fallback (get-or-create) ---------------------------------------


@pytest.mark.parametrize("command", ["capture", "add"])
def test_capture_plain_text_creates_task_in_auto_created_inbox(
    runner: CliRunner, command: str
) -> None:
    result = runner.invoke(app, [command, "buy", "milk"])
    assert result.exit_code == 0

    projects = _list_projects(runner)
    inbox_projects = [p for p in projects if p["name"] == "inbox"]
    assert len(inbox_projects) == 1

    tasks = _list_tasks(runner)
    assert len(tasks) == 1
    assert tasks[0]["title"] == "buy milk"
    assert tasks[0]["project_id"] == inbox_projects[0]["id"]


def test_capture_second_call_reuses_same_inbox(runner: CliRunner) -> None:
    runner.invoke(app, ["capture", "buy", "milk"])
    runner.invoke(app, ["capture", "buy", "eggs"])

    projects = _list_projects(runner)
    inbox_projects = [p for p in projects if p["name"] == "inbox"]
    assert len(inbox_projects) == 1

    tasks = _list_tasks(runner)
    assert len(tasks) == 2
    assert {t["project_id"] for t in tasks} == {inbox_projects[0]["id"]}


def test_capture_all_sigil_input_is_domain_validation_error_and_no_task_created(
    runner: CliRunner,
) -> None:
    result = runner.invoke(app, ["capture", "!high"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("domain_validation_error: ")

    tasks = _list_tasks(runner)
    assert len(tasks) == 0


# --- project resolution via #name ------------------------------------------


def test_capture_hash_token_targets_existing_project_case_insensitive(
    runner: CliRunner,
) -> None:
    project_id = _create_project(runner, "Casa")

    result = runner.invoke(app, ["capture", "buy", "milk", "#casa"])
    assert result.exit_code == 0

    tasks = _list_tasks(runner)
    assert len(tasks) == 1
    assert tasks[0]["project_id"] == project_id
    assert tasks[0]["title"] == "buy milk"


def test_capture_hash_token_nonexistent_project_exits_1(runner: CliRunner) -> None:
    result = runner.invoke(app, ["capture", "buy", "milk", "#nonexistent"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("project_name_not_found: ")

    tasks = _list_tasks(runner)
    assert len(tasks) == 0


def test_capture_hash_token_ambiguous_project_exits_1_with_ids(
    runner: CliRunner, db_session
) -> None:
    from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
        SQLiteProjectRepository,
    )

    repo = SQLiteProjectRepository(db_session)
    project_a = Project.create("Casa")
    project_b = Project.create("Casa")
    repo.add(project_a)
    repo.add(project_b)

    result = runner.invoke(app, ["capture", "buy", "milk", "#casa"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith("ambiguous_project_name: ")
    assert str(project_a.id) in result.stderr
    assert str(project_b.id) in result.stderr


# --- quick-add token integration -------------------------------------------


def test_capture_priority_and_due_date_tokens_land_on_task(runner: CliRunner) -> None:
    result = runner.invoke(
        app, ["--json", "capture", "buy", "milk", "!high", "@2026-08-03"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["title"] == "buy milk"
    assert payload["priority"] == "high"
    assert payload["due_date"] == "2026-08-03"


def test_capture_multi_arg_unquoted_invocation_joins_with_spaces(
    runner: CliRunner,
) -> None:
    result = runner.invoke(app, ["--json", "capture", "buy", "milk", "and", "eggs"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["title"] == "buy milk and eggs"
