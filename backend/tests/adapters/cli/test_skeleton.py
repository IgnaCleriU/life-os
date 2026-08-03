"""Tests del esqueleto del adaptador CLI: app typer, --json global, deps
wiring, traducción de errores y serializers.

Sigue el mismo espíritu que `tests/adapters/mcp/test_tools.py`: cada helper
de `deps` se prueba end-to-end contra el engine de test (no se mockea el
caso de uso), para asegurar que el wiring real (repos + sesión) funciona.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
import typer
from typer.testing import CliRunner

from lifeos.adapters.cli import deps, errors, serializers
from lifeos.adapters.cli.main import app
from lifeos.domain import (
    DomainValidationError,
    Priority,
    Project,
    ProjectNotEmpty,
    ProjectNotFound,
    ProjectStatus,
    Task,
    TaskNotFound,
    TaskStatus,
)

# --- app skeleton ----------------------------------------------------------


def test_help_lists_project_and_task_subcommands(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "project" in result.stdout
    assert "task" in result.stdout


def test_json_flag_parses_before_subcommand_group(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--json", "project", "--help"])
    assert result.exit_code == 0


# --- deps wiring -------------------------------------------------------


def test_create_project_use_case_writes_through_test_engine(cli_env) -> None:
    with deps.create_project_use_case() as use_case:
        project = use_case.execute(name="Test project")
    assert project.name == "Test project"

    with deps.list_projects_use_case() as use_case:
        projects = use_case.execute()
    assert [p.id for p in projects] == [project.id]


def test_create_task_use_case_writes_through_test_engine(cli_env) -> None:
    with deps.create_project_use_case() as use_case:
        project = use_case.execute(name="Parent project")

    with deps.create_task_use_case() as use_case:
        task = use_case.execute(project_id=project.id, title="Test task")
    assert task.title == "Test task"

    with deps.list_tasks_use_case() as use_case:
        tasks = use_case.execute(project.id)
    assert [t.id for t in tasks] == [task.id]


ALL_DEPS_NAMES = [
    "create_project_use_case",
    "list_projects_use_case",
    "get_project_use_case",
    "update_project_use_case",
    "complete_project_use_case",
    "archive_project_use_case",
    "activate_project_use_case",
    "delete_project_use_case",
    "restore_project_use_case",
    "create_task_use_case",
    "list_tasks_use_case",
    "get_task_use_case",
    "update_task_use_case",
    "complete_task_use_case",
    "start_task_use_case",
    "reopen_task_use_case",
    "move_task_use_case",
    "delete_task_use_case",
    "restore_task_use_case",
]


@pytest.mark.parametrize("name", ALL_DEPS_NAMES)
def test_deps_helper_exists_and_is_callable(name: str) -> None:
    helper = getattr(deps, name)
    assert callable(helper)


# --- errors ----------------------------------------------------------------


def _build_throwaway_app() -> typer.Typer:
    """App typer descartable para probar `handle_domain_errors` aislado."""
    tiny_app = typer.Typer()

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_domain_validation_error() -> None:
        raise DomainValidationError("bad value")

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_project_not_found() -> None:
        raise ProjectNotFound(uuid4())

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_task_not_found() -> None:
        raise TaskNotFound(uuid4())

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_project_not_empty() -> None:
        raise ProjectNotEmpty(uuid4())

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_project_name_not_found() -> None:
        raise errors.ProjectNameNotFound("Groceries")

    @tiny_app.command()
    @errors.handle_domain_errors
    def raise_ambiguous_project_name() -> None:
        raise errors.AmbiguousProjectName("Home", [uuid4(), uuid4()])

    @tiny_app.command()
    @errors.handle_domain_errors
    def succeed() -> None:
        typer.echo("ok")

    return tiny_app


@pytest.mark.parametrize(
    ("command", "expected_code"),
    [
        ("raise-domain-validation-error", "domain_validation_error"),
        ("raise-project-not-found", "project_not_found"),
        ("raise-task-not-found", "task_not_found"),
        ("raise-project-not-empty", "project_not_empty"),
        ("raise-project-name-not-found", "project_name_not_found"),
        ("raise-ambiguous-project-name", "ambiguous_project_name"),
    ],
)
def test_handle_domain_errors_maps_exception_to_exit_1(
    command: str, expected_code: str
) -> None:
    tiny_app = _build_throwaway_app()
    tiny_runner = CliRunner()
    result = tiny_runner.invoke(tiny_app, [command])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr.startswith(f"{expected_code}: ")


def test_handle_domain_errors_success_path_exits_0() -> None:
    tiny_app = _build_throwaway_app()
    tiny_runner = CliRunner()
    result = tiny_runner.invoke(tiny_app, ["succeed"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"


def test_project_name_not_found_message_contains_name() -> None:
    exc = errors.ProjectNameNotFound("Groceries")
    assert "Groceries" in str(exc)


def test_ambiguous_project_name_message_lists_candidates() -> None:
    id1, id2 = uuid4(), uuid4()
    exc = errors.AmbiguousProjectName("Home", [id1, id2])
    assert str(id1) in str(exc)
    assert str(id2) in str(exc)


# --- serializers -------------------------------------------------------


def _sample_project() -> Project:
    return Project(
        id=uuid4(),
        name="Sample",
        description="A description",
        status=ProjectStatus.ACTIVE,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _sample_task() -> Task:
    return Task(
        id=uuid4(),
        project_id=uuid4(),
        title="Sample task",
        description=None,
        status=TaskStatus.TODO,
        priority=Priority.HIGH,
        due_date=date(2026, 2, 1),
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_project_dict_matches_mcp_field_set() -> None:
    project = _sample_project()
    result = serializers.project_dict(project)
    assert result == {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
        "position": project.position,
    }


def test_task_dict_matches_mcp_field_set() -> None:
    task = _sample_task()
    result = serializers.task_dict(task)
    assert result == {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": task.due_date.isoformat(),
        "created_at": task.created_at.isoformat(),
    }


def test_task_dict_due_date_none_passthrough() -> None:
    task = _sample_task()
    task.due_date = None
    result = serializers.task_dict(task)
    assert result["due_date"] is None


def test_format_project_returns_string_with_key_fields() -> None:
    project = _sample_project()
    text = serializers.format_project(project)
    assert isinstance(text, str)
    assert str(project.id) in text
    assert project.name in text
    assert project.status.value in text


def test_format_task_returns_string_with_key_fields() -> None:
    task = _sample_task()
    text = serializers.format_task(task)
    assert isinstance(text, str)
    assert str(task.id) in text
    assert task.title in text
    assert task.priority.value in text
    assert task.due_date.isoformat() in text


def test_format_projects_one_line_per_project() -> None:
    projects = [_sample_project(), _sample_project()]
    text = serializers.format_projects(projects)
    lines = text.splitlines()
    assert len(lines) == 2


def test_format_tasks_one_line_per_task() -> None:
    tasks = [_sample_task(), _sample_task()]
    text = serializers.format_tasks(tasks)
    lines = text.splitlines()
    assert len(lines) == 2
