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
