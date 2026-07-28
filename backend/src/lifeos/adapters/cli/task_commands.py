"""Comandos `lifeos task ...`, cada uno reutilizando el mismo caso de uso
que su endpoint REST/tool MCP equivalente (ver ADR 0002). Los handlers son
delgados: parsean argumentos vía typer, llaman al caso de uso, y formatean el
resultado según el flag `--json` global (guardado en `ctx.obj`).
"""

from __future__ import annotations

import json
from datetime import date
from uuid import UUID

import typer

from lifeos.adapters.cli import deps
from lifeos.adapters.cli.errors import handle_domain_errors
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
    if ctx.obj["json"]:
        typer.echo(json.dumps(task_dict(task)))
    else:
        typer.echo(format_task(task))


def _emit_tasks(ctx: typer.Context, tasks: list[Task]) -> None:
    if ctx.obj["json"]:
        typer.echo(json.dumps([task_dict(task) for task in tasks]))
    elif tasks:
        typer.echo(format_tasks(tasks))


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
