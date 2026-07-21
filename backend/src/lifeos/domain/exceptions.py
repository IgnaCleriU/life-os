"""Excepciones de dominio.

Son Python puro: no dependen de FastAPI, SQLite ni MCP. Las capas externas
(adaptadores REST/MCP) son las encargadas de traducirlas a respuestas HTTP o
mensajes para el agente.
"""

from __future__ import annotations

from uuid import UUID


class DomainError(Exception):
    """Base de todas las excepciones de dominio de Life OS."""


class DomainValidationError(DomainError):
    """Se viola una invariante del dominio (ej. nombre/título vacío)."""


class ProjectNotFound(DomainError):
    """No existe un proyecto con el id buscado."""

    def __init__(self, project_id: UUID) -> None:
        self.project_id = project_id
        super().__init__(f"No existe el proyecto con id {project_id}")


class TaskNotFound(DomainError):
    """No existe una tarea con el id buscado."""

    def __init__(self, task_id: UUID) -> None:
        self.task_id = task_id
        super().__init__(f"No existe la tarea con id {task_id}")
