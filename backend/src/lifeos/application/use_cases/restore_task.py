"""Caso de uso: restaurar una Task borrada.

Es el inverso de `DeleteTask`, y lo que hace que `u` (deshacer) en la TUI sea
barato. Es el único camino —junto con `RestoreProject`— que lee con
`include_deleted`: ningún listado expone tareas borradas.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository, TaskRepository
from lifeos.domain import ProjectNotFound, Task, TaskNotFound


class RestoreTask:
    """Deshace el borrado lógico de una tarea."""

    def __init__(
        self, task_repo: TaskRepository, project_repo: ProjectRepository
    ) -> None:
        self._task_repo = task_repo
        self._project_repo = project_repo

    def execute(self, task_id: UUID) -> Task:
        """Quita la marca de borrado y persiste el cambio.

        Falla si el proyecto padre no existe o está borrado: `DeleteProject`
        solo permite borrar un proyecto sin tareas vivas, así que restaurar una
        tarea ahí la dejaría huérfana —visible en los listados de tareas pero
        colgando de un proyecto invisible—, deshaciendo esa invariante por la
        puerta de atrás.
        """
        task = self._task_repo.get(task_id, include_deleted=True)
        if task is None:
            raise TaskNotFound(task_id)
        if self._project_repo.get(task.project_id) is None:
            raise ProjectNotFound(task.project_id)

        task.restore()
        self._task_repo.update(task)
        return task
