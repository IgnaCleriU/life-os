"""Comandos `lifeos task ...`, cada uno reutilizando el mismo caso de uso
que su endpoint REST/tool MCP equivalente (ver ADR 0002). Los handlers son
delgados: parsean argumentos vía typer, llaman al caso de uso, y formatean el
resultado según el flag `--json` global (guardado en `ctx.obj`).
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

import typer

from lifeos.adapters.cli import deps
from lifeos.adapters.cli.errors import handle_domain_errors
from lifeos.adapters.cli.output import emit_many, emit_single
from lifeos.adapters.cli.serializers import format_task, format_tasks, task_dict
from lifeos.domain import Priority, Task, TaskStatus

task_app = typer.Typer(help="Manage tasks.")


def _parse_date(value: str | None, param_name: str) -> date | None:
    """Parsea una fecha ISO (`YYYY-MM-DD`); no la sintaxis rápida `@...`."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{param_name} must be an ISO date (YYYY-MM-DD)."
        ) from exc


def _emit_task(ctx: typer.Context, task: Task) -> None:
    emit_single(ctx, task, task_dict, format_task)


def _emit_tasks(ctx: typer.Context, tasks: list[Task]) -> None:
    emit_many(ctx, tasks, task_dict, format_tasks)


@task_app.command("create")
@handle_domain_errors
def create(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Parent project id."),
    title: str = typer.Argument(..., help="Task title."),
    priority: Priority = typer.Option(
        Priority.MEDIUM, "--priority", help="Task priority."
    ),
    due: str | None = typer.Option(
        None, "--due", help="Due date (ISO format, YYYY-MM-DD)."
    ),
    description: str | None = typer.Option(
        None, "--description", help="Optional task description."
    ),
) -> None:
    """Create a new task under an existing project."""
    due_date = _parse_date(due, "--due")

    with deps.create_task_use_case() as use_case:
        task = use_case.execute(
            project_id,
            title,
            priority=priority,
            due_date=due_date,
            description=description,
        )
    _emit_task(ctx, task)


@task_app.command("list")
@handle_domain_errors
def list_(
    ctx: typer.Context,
    project: UUID | None = typer.Option(
        None, "--project", help="Filter by parent project id (all projects if omitted)."
    ),
    status: list[TaskStatus] = typer.Option(
        None, "--status", help="Filter by status (repeatable)."
    ),
    due_before: str | None = typer.Option(
        None, "--due-before", help="Filter by due date before (ISO format, YYYY-MM-DD)."
    ),
    text: str | None = typer.Option(
        None, "--text", help="Filter by text search in title/description."
    ),
) -> None:
    """List tasks, optionally filtered by project, status, due date and/or text."""
    due_before_date = _parse_date(due_before, "--due-before")

    with deps.list_tasks_use_case() as use_case:
        tasks = use_case.execute(
            project, statuses=status or None, due_before=due_before_date, text=text
        )
    _emit_tasks(ctx, tasks)


@task_app.command("show")
@handle_domain_errors
def show(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
) -> None:
    """Show a single task by id."""
    with deps.get_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)


@task_app.command("update")
@handle_domain_errors
def update(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
    title: str | None = typer.Option(None, "--title", help="New task title."),
    description: str | None = typer.Option(
        None, "--description", help="New task description."
    ),
    clear_description: bool = typer.Option(
        False,
        "--clear-description",
        help="Clear the task description (mutually exclusive with --description).",
    ),
    priority: Priority | None = typer.Option(
        None, "--priority", help="New task priority."
    ),
    due: str | None = typer.Option(
        None, "--due", help="New due date (ISO format, YYYY-MM-DD)."
    ),
    clear_due: bool = typer.Option(
        False,
        "--clear-due",
        help="Clear the task due date (mutually exclusive with --due).",
    ),
) -> None:
    """Update a task's title, description, priority and/or due date.

    An omitted `--description`/`--due` leaves that field untouched;
    `--clear-description`/`--clear-due` clears it explicitly. There is no
    `--clear-title`: the domain forbids empty titles.
    """
    if description is not None and clear_description:
        raise typer.BadParameter(
            "--description and --clear-description are mutually exclusive."
        )
    if due is not None and clear_due:
        raise typer.BadParameter("--due and --clear-due are mutually exclusive.")

    due_date = _parse_date(due, "--due")

    kwargs: dict[str, Any] = {"title": title, "priority": priority}
    if description is not None:
        kwargs["description"] = description
    elif clear_description:
        kwargs["description"] = None

    if due_date is not None:
        kwargs["due_date"] = due_date
    elif clear_due:
        kwargs["due_date"] = None

    with deps.update_task_use_case() as use_case:
        task = use_case.execute(task_id, **kwargs)
    _emit_task(ctx, task)


@task_app.command("complete")
@handle_domain_errors
def complete(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
) -> None:
    """Mark a task as completed (idempotent)."""
    with deps.complete_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)


@task_app.command("start")
@handle_domain_errors
def start(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
) -> None:
    """Mark a task as in progress."""
    with deps.start_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)


@task_app.command("reopen")
@handle_domain_errors
def reopen(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
) -> None:
    """Move a task back to pending."""
    with deps.reopen_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)


@task_app.command("move")
@handle_domain_errors
def move(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
    project_id: UUID = typer.Argument(..., help="Destination project id."),
) -> None:
    """Move a task to another existing project."""
    with deps.move_task_use_case() as use_case:
        task = use_case.execute(task_id, project_id)
    _emit_task(ctx, task)


@task_app.command("delete")
@handle_domain_errors
def delete(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt."
    ),
) -> None:
    """Delete a task (soft delete).

    The delete is soft: use `lifeos task restore` to undo it.
    """
    if not yes:
        typer.confirm(
            "This will soft-delete the task. It can be undone with "
            "'lifeos task restore'. Continue?",
            abort=True,
        )

    with deps.delete_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)


@task_app.command("restore")
@handle_domain_errors
def restore(
    ctx: typer.Context,
    task_id: UUID = typer.Argument(..., help="Task id."),
) -> None:
    """Undo the soft delete of a task."""
    with deps.restore_task_use_case() as use_case:
        task = use_case.execute(task_id)
    _emit_task(ctx, task)
