"""Comando `lifeos capture ...` (alias `lifeos add ...`): captura rápida de
tareas usando la sintaxis quick-add (ver ADR 0008 y
`adapters/shared/quick_add.py`).

Resolución del proyecto destino: la regla compartida con la TUI y REST de
`adapters/shared/capture_target.py`. Un `#nombre` se busca por nombre exacto
(case-insensitive); cero resultados levanta `ProjectNameNotFound` y más de
uno `AmbiguousProjectName` (el usuario desambigua con
`lifeos task create <project_id> ...`). Sin `#nombre`, el CLI no tiene un
proyecto por defecto, así que la tarea cae en "inbox", creado al vuelo si no
existe: la primera captura sin `#proyecto` en una base nueva lo crea.

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
from lifeos.adapters.cli.errors import handle_domain_errors
from lifeos.adapters.cli.output import emit_single
from lifeos.adapters.cli.serializers import format_task, task_dict
from lifeos.adapters.shared.capture_target import resolve_capture_target
from lifeos.adapters.shared.quick_add import parse_quick_add
from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.create_task import CreateTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)


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


def _run_capture(ctx: typer.Context, text: list[str]) -> None:
    joined_text = " ".join(text)
    parsed = parse_quick_add(joined_text)

    with _capture_use_cases() as use_cases:
        project = resolve_capture_target(
            parsed.project_name,
            list_projects=lambda text: use_cases.list_projects.execute(text=text),
            create_project=use_cases.create_project.execute,
        )

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
