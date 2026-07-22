"""Caso de uso: crear una nueva Task asociada a un Project.

Verifica que el proyecto padre exista antes de crear la tarea y la persiste a
través del `TaskRepository`. La validación del título vive en el dominio
(`Task.create`), que propaga `DomainValidationError` si es vacío.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from lifeos.application.ports import ProjectRepository, TaskRepository
from lifeos.domain import Priority, ProjectNotFound, Task


class CreateTask:
    """Crea una tarea nueva bajo un proyecto existente."""

    def __init__(
        self, task_repo: TaskRepository, project_repo: ProjectRepository
    ) -> None:
        self._task_repo = task_repo
        self._project_repo = project_repo

    def execute(
        self,
        project_id: UUID,
        title: str,
        priority: Priority = Priority.MEDIUM,
        due_date: date | None = None,
        description: str | None = None,
    ) -> Task:
        """Crea y persiste la tarea; falla si el proyecto padre no existe."""
        if self._project_repo.get(project_id) is None:
            raise ProjectNotFound(project_id)

        task = Task.create(
            project_id=project_id,
            title=title,
            priority=priority,
            due_date=due_date,
            description=description,
        )
        self._task_repo.add(task)
        return task
