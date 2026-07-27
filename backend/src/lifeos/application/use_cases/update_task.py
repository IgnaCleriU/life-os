"""Caso de uso: actualizar los datos de una Task existente.

Actualización parcial: solo se modifican los campos provistos. Para `due_date`
se usa un centinela (`_UNSET`) que distingue "no tocar la fecha" de "poner la
fecha en None" (quitarla). Las invariantes (título no vacío) las valida el
dominio a través de los métodos de `Task`.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.application.ports import TaskRepository
from lifeos.domain import Priority, Task, TaskNotFound

_UNSET = object()


class UpdateTask:
    """Actualiza parcialmente los datos de una tarea existente."""

    def __init__(self, task_repo: TaskRepository) -> None:
        self._task_repo = task_repo

    def execute(
        self,
        task_id: UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        due_date: date | None | object = _UNSET,
    ) -> Task:
        """Aplica solo los campos provistos y persiste la tarea."""
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)

        if title is not None:
            task.rename(title)
        if priority is not None:
            task.change_priority(priority)
        if due_date is not _UNSET:
            task.reschedule(due_date)  # type: ignore[arg-type]
        if description is not None:
            task.description = description

        self._task_repo.update(task)
        return task
