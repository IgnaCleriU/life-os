"""Puerto de persistencia de Project.

Interfaz abstracta (`Protocol`) que define cómo los casos de uso persisten y
consultan `Project`, sin atarse a SQLite ni a ningún motor concreto. La
implementación real vive en `infrastructure/`; los tests usan un fake en
memoria.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from lifeos.domain import Project


class ProjectRepository(Protocol):
    """Contrato de persistencia para la entidad `Project`."""

    def add(self, project: Project) -> None:
        """Persiste un proyecto nuevo."""
        ...

    def get(self, project_id: UUID) -> Project | None:
        """Devuelve el proyecto con ese id, o `None` si no existe."""
        ...

    def list_all(self) -> list[Project]:
        """Devuelve todos los proyectos."""
        ...
