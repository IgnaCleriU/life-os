"""Caso de uso: reabrir una Task.

Transiciona la tarea de vuelta a estado TODO (la transición vive en el
dominio) y persiste el cambio a través del `TaskRepository`.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskNotFound


class ReopenTask:
    """Vuelve una tarea existente a pendiente."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, task_id: UUID) -> Task:
        """Reabre la tarea y persiste el cambio; falla si no existe."""
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)

        task.reopen()
        self._task_repo.update(task)
        return task
