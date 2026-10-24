"""Caso de uso: borrar una Task.

El borrado es lógico: se marca `deleted_at` y la tarea desaparece de todas las
lecturas, pero la fila sigue ahí. Así `RestoreTask` es un cambio de campo y no
una reconstrucción de la entidad —`Task.create()` genera su propio id, con lo
cual restaurar un borrado físico no devolvería la misma tarea.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Task, TaskNotFound


class DeleteTask:
    """Borra lógicamente una tarea existente."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(self, task_id: UUID) -> Task:
        """Marca la tarea como borrada y persiste el cambio."""
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)

        task.delete()
        self._task_repo.update(task)
        return task
