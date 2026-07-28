"""Repositorios fake en memoria para testear los casos de uso sin base de datos.

Implementan estructuralmente los puertos `ProjectRepository` y `TaskRepository`
(ver `lifeos.application.ports`). Guardan las entidades en un dict por id, sin
copiarlas: los casos de uso operan sobre las mismas instancias de dominio.

Replican el filtrado de borrados lógicos de los repositorios SQLite. Eso no es
opcional: si los fakes mostraran entidades borradas, cada test de caso de uso
estaría verificando un contrato que la implementación real no cumple.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from lifeos.domain import Project, ProjectStatus, Task, TaskStatus


class InMemoryProjectRepository:
    """`ProjectRepository` en memoria para tests."""

    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}

    def add(self, project: Project) -> None:
        self._projects[project.id] = project

    def get(
        self, project_id: UUID, *, include_deleted: bool = False
    ) -> Project | None:
        project = self._projects.get(project_id)
        if project is None or (project.is_deleted and not include_deleted):
            return None
        return project

    def list(
        self,
        *,
        statuses: Sequence[ProjectStatus] | None = None,
        text: str | None = None,
    ) -> list[Project]:
        return [
            project
            for project in self._projects.values()
            if not project.is_deleted
            and (statuses is None or project.status in statuses)
            and (text is None or text.lower() in project.name.lower())
        ]

    def update(self, project: Project) -> None:
        self._projects[project.id] = project


class InMemoryTaskRepository:
    """`TaskRepository` en memoria para tests."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: UUID, *, include_deleted: bool = False) -> Task | None:
        task = self._tasks.get(task_id)
        if task is None or (task.is_deleted and not include_deleted):
            return None
        return task

    def list(
        self,
        *,
        project_id: UUID | None = None,
        statuses: Sequence[TaskStatus] | None = None,
        due_before: date | None = None,
        text: str | None = None,
    ) -> list[Task]:
        return [
            task
            for task in self._tasks.values()
            if not task.is_deleted
            and (project_id is None or task.project_id == project_id)
            and (statuses is None or task.status in statuses)
            and (
                due_before is None
                or (task.due_date is not None and task.due_date <= due_before)
            )
            and (text is None or text.lower() in task.title.lower())
        ]

    def update(self, task: Task) -> None:
        self._tasks[task.id] = task
