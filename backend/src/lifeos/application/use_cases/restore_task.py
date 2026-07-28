"""Caso de uso: restaurar una Task borrada.

Es el inverso de `DeleteTask`, y lo que hace que `u` (deshacer) en la TUI sea
barato. Es el único camino —junto con `RestoreProject`— que lee con
`include_deleted`: ningún listado expone tareas borradas.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskNotFound


class RestoreTask:
    """Deshace el borrado lógico de una tarea."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, task_id: UUID) -> Task:
        """Quita la marca de borrado y persiste el cambio."""
        task = self._task_repo.get(task_id, include_deleted=True)
        if task is None:
            raise TaskNotFound(task_id)

        task.restore()
        self._task_repo.update(task)
        return task
