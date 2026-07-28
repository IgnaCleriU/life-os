"""Comandos `lifeos project ...`, cada uno reutilizando el mismo caso de uso
que su endpoint REST/tool MCP equivalente (ver ADR 0002). Los handlers son
delgados: parsean argumentos vía typer, llaman al caso de uso, y formatean el
resultado según el flag `--json` global (guardado en `ctx.obj`).
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import typer

from lifeos.adapters.cli import deps
from lifeos.adapters.cli.errors import handle_domain_errors
from lifeos.adapters.cli.serializers import (
    format_project,
    format_projects,
    project_dict,
)
from lifeos.domain import Project, ProjectStatus

# Centinela para distinguir "el usuario no mandó la opción" (no tocar el
# campo) de "la mandó vacía" — mismo patrón que `_UNSET` en `adapters/mcp/
# tools.py`.
_UNSET: Any = object()

project_app = typer.Typer(help="Manage projects.")


def _emit_project(ctx: typer.Context, project: Project) -> None:
    if ctx.obj["json"]:
        typer.echo(json.dumps(project_dict(project)))
    else:
        typer.echo(format_project(project))


def _emit_projects(ctx: typer.Context, projects: list[Project]) -> None:
    if ctx.obj["json"]:
        typer.echo(json.dumps([project_dict(project) for project in projects]))
    elif projects:
        typer.echo(format_projects(projects))


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
