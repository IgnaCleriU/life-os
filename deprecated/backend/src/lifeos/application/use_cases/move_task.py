"""Caso de uso: mover una Task a otro Project.

Valida que el proyecto destino exista —igual que hace `CreateTask`— antes de
delegar la transición en el dominio.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository, TaskRepository
from lifeos.domain import ProjectNotFound, Task, TaskNotFound


class MoveTask:
    """Mueve una tarea existente a otro proyecto existente."""

    def __init__(
        self, task_repo: TaskRepository, project_repo: ProjectRepository
    ) -> None:
        self._task_repo = task_repo
        self._project_repo = project_repo

    def execute(self, task_id: UUID, project_id: UUID) -> Task:
        """Mueve la tarea al proyecto destino y persiste el cambio.

        Falla si la tarea o el proyecto destino no existen, y en ese caso no
        modifica nada.
        """
        task = self._task_repo.get(task_id)
        if task is None:
            raise TaskNotFound(task_id)
        if self._project_repo.get(project_id) is None:
            raise ProjectNotFound(project_id)

        task.move_to(project_id)
        self._task_repo.update(task)
        return task
