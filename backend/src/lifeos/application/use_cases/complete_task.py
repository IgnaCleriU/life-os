"""Caso de uso: marcar una Task como completada.

Transiciona la tarea a estado DONE (la transición vive en el dominio) y
persiste el cambio a través del `TaskRepository`.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskNotFound


class CompleteTask:
    """Marca una tarea existente como completada."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, task_id: UUID) -> Task:
        """Completa la tarea y persiste el cambio; falla si no existe."""
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)

        task.complete()
        self._task_repo.update(task)
        return task
