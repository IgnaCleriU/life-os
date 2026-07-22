"""Repositorios fake en memoria para testear los casos de uso sin base de datos.

Implementan estructuralmente los puertos `ProjectRepository` y `TaskRepository`
(ver `lifeos.application.ports`). Guardan las entidades en un dict por id, sin
copiarlas: los casos de uso operan sobre las mismas instancias de dominio.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.domain import Project, Task


class InMemoryProjectRepository:
    """`ProjectRepository` en memoria para tests."""

    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}

    def add(self, project: Project) -> None:
        self._projects[project.id] = project

    def get(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    def list_all(self) -> list[Project]:
        return list(self._projects.values())


class InMemoryTaskRepository:
    """`TaskRepository` en memoria para tests."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    def add(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    def list_by_project(self, project_id: UUID) -> list[Task]:
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def update(self, task: Task) -> None:
        self._tasks[task.id] = task
