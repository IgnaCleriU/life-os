"""Puerto de persistencia de Task.

Interfaz abstracta (`Protocol`) que define cómo los casos de uso persisten y
consultan `Task`, sin atarse a SQLite ni a ningún motor concreto. La
implementación real vive en `infrastructure/`; los tests usan un fake en
memoria.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from lifeos.domain import Task


class TaskRepository(Protocol):
    """Contrato de persistencia para la entidad `Task`."""

    def add(self, task: Task) -> None:
        """Persiste una tarea nueva."""
        ...

    def get(self, task_id: UUID) -> Task | None:
        """Devuelve la tarea con ese id, o `None` si no existe."""
        ...

    def list_by_project(self, project_id: UUID) -> list[Task]:
        """Devuelve las tareas de un proyecto."""
        ...

    def update(self, task: Task) -> None:
        """Persiste los cambios de una tarea existente."""
        ...
