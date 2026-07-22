"""Caso de uso: listar las Task de un Project.

Consulta las tareas de un proyecto a través del `TaskRepository`, sin aplicar
reglas de negocio adicionales.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task


class ListTasks:
    """Lista las tareas pertenecientes a un proyecto."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, project_id: UUID) -> list[Task]:
        """Devuelve las tareas del proyecto indicado."""
        return self._task_repo.list_by_project(project_id)
