"""Caso de uso: obtener una Task por id.

Lo necesita el panel de detalle de la TUI, que muestra una tarea concreta sin
volver a listar todo el proyecto.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskNotFound


class GetTask:
    """Devuelve una tarea existente por su id."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, task_id: UUID) -> Task:
        """Devuelve la tarea; falla si no existe o está borrada."""
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)

        return task
