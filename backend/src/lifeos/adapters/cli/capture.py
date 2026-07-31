"""Comando `lifeos capture ...` (alias `lifeos add ...`): captura rápida de
tareas usando la sintaxis quick-add (ver ADR 0008 y
`adapters/shared/quick_add.py`).

Resolución del proyecto destino:

- Si el texto trae `#nombre`, se busca un proyecto cuyo nombre matchee
  exactamente (case-insensitive, `casefold` + `strip`) contra ese nombre.
  Cero resultados levanta `ProjectNameNotFound`; más de uno (dos proyectos
  activos con el mismo nombre) levanta `AmbiguousProjectName` listando los
  ids candidatos, para que el usuario desambigüe con
  `lifeos task create <project_id> ...` en vez de `capture`.
- Si no hay `#nombre`, se usa como destino un proyecto "inbox" que se
  busca por el mismo matcheo exacto y, si no existe, se crea al vuelo
  (get-or-create). Esto significa que la primera captura sin `#proyecto`
  en una base nueva crea el proyecto "inbox" automáticamente.

Nota sobre la carrera get-or-create: esta app es de un solo usuario y no
hay locking explícito entre el `list` y el `create` del inbox, así que en
teoría dos capturas concurrentes podrían pasar ambas por "no existe
todavía" y crear dos proyectos "inbox". Se acepta este TOCTOU (time-of-
check to time-of-use) porque el caso de uso real es un usuario disparando
comandos en serie desde una terminal; si llegara a pasar, es recuperable
a mano (mover las tareas del inbox duplicado y borrar uno de los dos
proyectos).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import typer

from lifeos.adapters.cli import deps
from lifeos.adapters.cli.errors import (
    AmbiguousProjectName,
    ProjectNameNotFound,
    handle_domain_errors,
)
from lifeos.adapters.cli.output import emit_single
from lifeos.adapters.cli.serializers import format_task, task_dict
from lifeos.adapters.shared.quick_add import parse_quick_add
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.domain import Project
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)

_INBOX_PROJECT_NAME = "inbox"


@dataclass(frozen=True)
class _CaptureUseCases:
    list_projects: ListProjects
    create_project: CreateProject
    create_task: CreateTask


@contextmanager
def _capture_use_cases() -> Iterator[_CaptureUseCases]:
    """Abre una única sesión de DB con los tres casos de uso que necesita
    `capture`: resolver/crear el proyecto destino y crear la tarea."""
    with deps.get_session() as session:
        project_repo = SQLiteProjectRepository(session)
        task_repo = SQLiteTaskRepository(session)
        yield _CaptureUseCases(
            list_projects=ListProjects(project_repo),
            create_project=CreateProject(project_repo),
            create_task=CreateTask(task_repo, project_repo),
        )


def _find_exact_match(projects: list[Project], name: str) -> list[Project]:
    target = name.strip().casefold()
    return [p for p in projects if p.name.strip().casefold() == target]


def _resolve_project(use_cases: _CaptureUseCases, name: str) -> Project:
    """Busca un proyecto por nombre exacto (case-insensitive).

    Usado tanto para `#nombre` explícito como para el fallback "inbox".
    """
    candidates = use_cases.list_projects.execute(text=name)
    matches = _find_exact_match(candidates, name)

    if not matches:
        raise ProjectNameNotFound(name)
    if len(matches) > 1:
        raise AmbiguousProjectName(name, [p.id for p in matches])
    return matches[0]


def _resolve_or_create_inbox(use_cases: _CaptureUseCases) -> Project:
    try:
        return _resolve_project(use_cases, _INBOX_PROJECT_NAME)
    except ProjectNameNotFound:
        return use_cases.create_project.execute(_INBOX_PROJECT_NAME)


def _run_capture(ctx: typer.Context, text: list[str]) -> None:
    joined_text = " ".join(text)
    parsed = parse_quick_add(joined_text)

    with _capture_use_cases() as use_cases:
        if parsed.project_name is not None:
            project = _resolve_project(use_cases, parsed.project_name)
        else:
            project = _resolve_or_create_inbox(use_cases)

        task = use_cases.create_task.execute(
            project.id,
            parsed.title,
            priority=parsed.priority,
            due_date=parsed.due_date,
        )

    emit_single(ctx, task, task_dict, format_task)


@handle_domain_errors
def capture(
    ctx: typer.Context,
    text: list[str] = typer.Argument(..., help="Quick-add text to capture."),
) -> None:
    """Capture a task from free-form quick-add text.

    Parses `!low`/`!med`/`!high` priority, `@today`/`@tomorrow`/weekday/
    ISO due dates and `#project` tokens (see the quick-add ADR). Tasks
    without `#project` land in an auto-created "inbox" project.
    """
    _run_capture(ctx, text)
