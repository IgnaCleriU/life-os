"""Tools MCP de Project y Task, cada una reutilizando el mismo caso de uso
que su endpoint REST equivalente (ver ADR 0002). Los handlers son delgados:
parsean argumentos (Pydantic, vía las anotaciones de tipo de FastMCP), llaman
al caso de uso, y formatean el resultado como dict — la traducción de
protocolo propia de este adaptador, independiente de `adapters/rest/schemas.py`.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from lifeos.adapters.mcp import deps
from lifeos.domain import (
    DomainValidationError,
    Priority,
    Project,
    ProjectNotFound,
    Task,
    TaskNotFound,
)

# Centinela para distinguir "el cliente no mandó `due_date`" (no tocar la
# fecha) de "el cliente mandó `due_date: null`" (limpiarla) — mismo problema
# que resuelve `_UNSET` en `UpdateTask.execute`. A diferencia de esa función,
# acá se anota como `date | None` (sin `object` en el union): así Pydantic
# sigue coercionando un `due_date` explícito a `date`, y como Pydantic no
# valida los valores default, el centinela pasa intacto cuando se omite.
_UNSET: Any = object()

_DOMAIN_ERROR_CODES: dict[type[Exception], str] = {
    DomainValidationError: "domain_validation_error",
    ProjectNotFound: "project_not_found",
    TaskNotFound: "task_not_found",
}


def _as_tool_error(exc: Exception) -> ToolError:
    code = _DOMAIN_ERROR_CODES[type(exc)]
    return ToolError(f"{code}: {exc}")


def _project_dict(project: Project) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
    }


def _task_dict(task: Task) -> dict[str, Any]:
    return {
        "id": str(task.id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


def register_tools(server: FastMCP) -> None:
    """Registra las tools de Project y Task en la instancia de FastMCP dada."""

    @server.tool()
    def create_project(name: str, description: str | None = None) -> dict[str, Any]:
        """Crea un proyecto nuevo."""
        try:
            with deps.create_project_use_case() as use_case:
                project = use_case.execute(name=name, description=description)
        except DomainValidationError as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def list_projects() -> list[dict[str, Any]]:
        """Lista todos los proyectos."""
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute()
        return [_project_dict(project) for project in projects]

    @server.tool()
    def create_task(
        project_id: UUID,
        title: str,
        priority: Priority = Priority.MEDIUM,
        due_date: date | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Crea una tarea bajo un proyecto existente."""
        try:
            with deps.create_task_use_case() as use_case:
                task = use_case.execute(
                    project_id=project_id,
                    title=title,
                    priority=priority,
                    due_date=due_date,
                    description=description,
                )
        except (ProjectNotFound, DomainValidationError) as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def list_tasks(project_id: UUID) -> list[dict[str, Any]]:
        """Lista las tareas de un proyecto."""
        with deps.list_tasks_use_case() as use_case:
            tasks = use_case.execute(project_id)
        return [_task_dict(task) for task in tasks]

    @server.tool()
    def update_task(
        task_id: UUID,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        due_date: date | None = _UNSET,
    ) -> dict[str, Any]:
        """Actualiza parcialmente una tarea.

        Un `due_date` omitido no toca la fecha existente; `due_date: null`
        explícito sí la limpia — misma semántica que `PATCH /tasks/{id}` en
        REST. `UpdateTask.execute` tiene su propio centinela `_UNSET`
        (distinto por identidad del de este módulo), así que un `due_date`
        omitido acá no debe reenviarse: se deja que el caso de uso use su
        propio default.
        """
        kwargs: dict[str, Any] = {
            "title": title,
            "description": description,
            "priority": priority,
        }
        if due_date is not _UNSET:
            kwargs["due_date"] = due_date
        try:
            with deps.update_task_use_case() as use_case:
                task = use_case.execute(task_id, **kwargs)
        except (TaskNotFound, DomainValidationError) as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def complete_task(task_id: UUID) -> dict[str, Any]:
        """Marca una tarea como completada (idempotente)."""
        try:
            with deps.complete_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except TaskNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)
