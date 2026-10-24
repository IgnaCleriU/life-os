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
from lifeos.adapters.shared.error_codes import DOMAIN_ERROR_CODES
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

# Centinela para distinguir "el cliente no mandó el campo" (no tocarlo) de
# "el cliente mandó el campo en null" (limpiarlo) — mismo problema que
# resuelve `_UNSET` en `UpdateTask.execute`/`UpdateProject.execute`. A
# diferencia de esas funciones, acá se anota sin `object` en el union: así
# Pydantic sigue coercionando un valor explícito al tipo declarado, y como
# Pydantic no valida los valores default, el centinela pasa intacto cuando
# se omite.
_UNSET: Any = object()

_DOMAIN_ERROR_CODES = DOMAIN_ERROR_CODES


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

    # --- Project ---------------------------------------------------------

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
    def list_projects(
        status: list[ProjectStatus] | None = None,
        text: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista proyectos, opcionalmente filtrados por estado y/o texto."""
        with deps.list_projects_use_case() as use_case:
            projects = use_case.execute(statuses=status, text=text)
        return [_project_dict(project) for project in projects]

    @server.tool()
    def get_project(project_id: UUID) -> dict[str, Any]:
        """Devuelve un proyecto por id."""
        try:
            with deps.get_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except ProjectNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def update_project(
        project_id: UUID,
        name: str | None = None,
        description: str | None = _UNSET,
    ) -> dict[str, Any]:
        """Actualiza parcialmente un proyecto.

        Un `description` omitido no toca la descripción existente;
        `description: null` explícito sí la limpia — misma semántica que
        `PATCH /projects/{id}` en REST.
        """
        kwargs: dict[str, Any] = {"name": name}
        if description is not _UNSET:
            kwargs["description"] = description
        try:
            with deps.update_project_use_case() as use_case:
                project = use_case.execute(project_id, **kwargs)
        except (ProjectNotFound, DomainValidationError) as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def complete_project(project_id: UUID) -> dict[str, Any]:
        """Marca un proyecto como finalizado (idempotente)."""
        try:
            with deps.complete_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except ProjectNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def archive_project(project_id: UUID) -> dict[str, Any]:
        """Archiva un proyecto (idempotente)."""
        try:
            with deps.archive_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except ProjectNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def activate_project(project_id: UUID) -> dict[str, Any]:
        """Reactiva un proyecto (idempotente)."""
        try:
            with deps.activate_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except ProjectNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def delete_project(project_id: UUID) -> dict[str, Any]:
        """Borra lógicamente un proyecto; falla si todavía tiene tareas vivas."""
        try:
            with deps.delete_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except (ProjectNotFound, ProjectNotEmpty) as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    @server.tool()
    def restore_project(project_id: UUID) -> dict[str, Any]:
        """Deshace el borrado lógico de un proyecto."""
        try:
            with deps.restore_project_use_case() as use_case:
                project = use_case.execute(project_id)
        except ProjectNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _project_dict(project)

    # --- Task ------------------------------------------------------------

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
    def list_tasks(
        project_id: UUID | None = None,
        status: list[TaskStatus] | None = None,
        due_before: date | None = None,
        text: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lista tareas, opcionalmente filtradas por proyecto, estado, fecha
        límite y/o texto. Sin `project_id`, lista de todos los proyectos.
        """
        with deps.list_tasks_use_case() as use_case:
            tasks = use_case.execute(
                project_id, statuses=status, due_before=due_before, text=text
            )
        return [_task_dict(task) for task in tasks]

    @server.tool()
    def get_task(task_id: UUID) -> dict[str, Any]:
        """Devuelve una tarea por id."""
        try:
            with deps.get_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except TaskNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def update_task(
        task_id: UUID,
        title: str | None = None,
        description: str | None = _UNSET,
        priority: Priority | None = None,
        due_date: date | None = _UNSET,
    ) -> dict[str, Any]:
        """Actualiza parcialmente una tarea.

        Un `due_date`/`description` omitido no toca el campo existente;
        `due_date: null`/`description: null` explícito sí lo limpia — misma
        semántica que `PATCH /tasks/{id}` en REST. `UpdateTask.execute` tiene
        su propio centinela `_UNSET` (distinto por identidad del de este
        módulo), así que un campo omitido acá no debe reenviarse: se deja que
        el caso de uso use su propio default.
        """
        kwargs: dict[str, Any] = {"title": title, "priority": priority}
        if description is not _UNSET:
            kwargs["description"] = description
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

    @server.tool()
    def start_task(task_id: UUID) -> dict[str, Any]:
        """Marca una tarea como en curso (idempotente)."""
        try:
            with deps.start_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except TaskNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def reopen_task(task_id: UUID) -> dict[str, Any]:
        """Vuelve una tarea a pendiente (idempotente)."""
        try:
            with deps.reopen_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except TaskNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def move_task(task_id: UUID, project_id: UUID) -> dict[str, Any]:
        """Mueve una tarea a otro proyecto."""
        try:
            with deps.move_task_use_case() as use_case:
                task = use_case.execute(task_id, project_id)
        except (TaskNotFound, ProjectNotFound) as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def delete_task(task_id: UUID) -> dict[str, Any]:
        """Borra lógicamente una tarea."""
        try:
            with deps.delete_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except TaskNotFound as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)

    @server.tool()
    def restore_task(task_id: UUID) -> dict[str, Any]:
        """Deshace el borrado lógico de una tarea.

        Falla si el proyecto padre no existe o sigue borrado.
        """
        try:
            with deps.restore_task_use_case() as use_case:
                task = use_case.execute(task_id)
        except (TaskNotFound, ProjectNotFound) as exc:
            raise _as_tool_error(exc) from exc
        return _task_dict(task)
