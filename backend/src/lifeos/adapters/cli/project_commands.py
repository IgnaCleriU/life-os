"""Comandos `lifeos project ...`, cada uno reutilizando el mismo caso de uso
que su endpoint REST/tool MCP equivalente (ver ADR 0002). Los handlers son
delgados: parsean argumentos vía typer, llaman al caso de uso, y formatean el
resultado según el flag `--json` global (guardado en `ctx.obj`).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import typer

from lifeos.adapters.cli import deps
from lifeos.adapters.cli.errors import handle_domain_errors
from lifeos.adapters.cli.output import emit_many, emit_single
from lifeos.adapters.cli.serializers import (
    format_project,
    format_projects,
    project_dict,
)
from lifeos.domain import Project, ProjectStatus

project_app = typer.Typer(help="Manage projects.")


def _emit_project(ctx: typer.Context, project: Project) -> None:
    emit_single(ctx, project, project_dict, format_project)


def _emit_projects(ctx: typer.Context, projects: list[Project]) -> None:
    emit_many(ctx, projects, project_dict, format_projects)


@project_app.command("create")
@handle_domain_errors
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Project name."),
    description: str | None = typer.Option(
        None, "--description", help="Optional project description."
    ),
) -> None:
    """Create a new project."""
    with deps.create_project_use_case() as use_case:
        project = use_case.execute(name=name, description=description)
    _emit_project(ctx, project)


@project_app.command("list")
@handle_domain_errors
def list_(
    ctx: typer.Context,
    status: list[ProjectStatus] = typer.Option(
        None, "--status", help="Filter by status (repeatable)."
    ),
    text: str | None = typer.Option(
        None, "--text", help="Filter by text search in name/description."
    ),
) -> None:
    """List projects, optionally filtered by status and/or text."""
    with deps.list_projects_use_case() as use_case:
        projects = use_case.execute(statuses=status or None, text=text)
    _emit_projects(ctx, projects)


@project_app.command("show")
@handle_domain_errors
def show(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Show a single project by id."""
    with deps.get_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("update")
@handle_domain_errors
def update(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
    name: str | None = typer.Option(None, "--name", help="New project name."),
    description: str | None = typer.Option(
        None, "--description", help="New project description."
    ),
    clear_description: bool = typer.Option(
        False,
        "--clear-description",
        help="Clear the project description (mutually exclusive with --description).",
    ),
) -> None:
    """Update a project's name and/or description.

    An omitted `--description` leaves the description untouched;
    `--clear-description` clears it explicitly. There is no
    `--clear-name`: the domain forbids empty names.
    """
    if description is not None and clear_description:
        raise typer.BadParameter(
            "--description and --clear-description are mutually exclusive."
        )

    kwargs: dict[str, Any] = {"name": name}
    if description is not None:
        kwargs["description"] = description
    elif clear_description:
        kwargs["description"] = None

    with deps.update_project_use_case() as use_case:
        project = use_case.execute(project_id, **kwargs)
    _emit_project(ctx, project)


@project_app.command("complete")
@handle_domain_errors
def complete(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Mark a project as completed (idempotent)."""
    with deps.complete_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("archive")
@handle_domain_errors
def archive(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Archive a project (idempotent)."""
    with deps.archive_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("activate")
@handle_domain_errors
def activate(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Reactivate a project (idempotent)."""
    with deps.activate_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("reorder-up")
@handle_domain_errors
def reorder_up(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Move a project up one place (no-op if it's already first)."""
    with deps.reorder_project_up_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("reorder-down")
@handle_domain_errors
def reorder_down(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Move a project down one place (no-op if it's already last)."""
    with deps.reorder_project_down_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("delete")
@handle_domain_errors
def delete(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt."
    ),
) -> None:
    """Delete a project (soft delete; fails if it still has live tasks).

    The delete is soft: use `lifeos project restore` to undo it.
    """
    if not yes:
        typer.confirm(
            "This will soft-delete the project. It can be undone with "
            "'lifeos project restore'. Continue?",
            abort=True,
        )

    with deps.delete_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)


@project_app.command("restore")
@handle_domain_errors
def restore(
    ctx: typer.Context,
    project_id: UUID = typer.Argument(..., help="Project id."),
) -> None:
    """Undo the soft delete of a project."""
    with deps.restore_project_use_case() as use_case:
        project = use_case.execute(project_id)
    _emit_project(ctx, project)
