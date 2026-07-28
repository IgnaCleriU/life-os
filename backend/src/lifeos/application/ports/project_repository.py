"""Puerto de persistencia de Project.

Interfaz abstracta (`Protocol`) que define cómo los casos de uso persisten y
consultan `Project`, sin atarse a SQLite ni a ningún motor concreto. La
implementación real vive en `infrastructure/`; los tests usan un fake en
memoria.

Los proyectos borrados (`deleted_at` no nulo) quedan fuera de todas las
lecturas salvo que se pida `include_deleted`, por el mismo motivo que en
`TaskRepository`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from lifeos.domain import Project, ProjectStatus


class ProjectRepository(Protocol):
    """Contrato de persistencia para la entidad `Project`."""

    def add(self, project: Project) -> None:
        """Persiste un proyecto nuevo."""
        ...

    def get(
        self, project_id: UUID, *, include_deleted: bool = False
    ) -> Project | None:
        """Devuelve el proyecto con ese id, o `None` si no existe.

        `include_deleted` existe sólo para que `RestoreProject` pueda alcanzar
        un proyecto borrado; ningún listado lo expone.
        """
        ...

    def list(
        self,
        *,
        statuses: Sequence[ProjectStatus] | None = None,
        text: str | None = None,
    ) -> list[Project]:
        """Devuelve los proyectos vivos que cumplen todos los filtros dados.

        Un filtro en `None` no restringe. `text` busca subcadena en el nombre,
        sin distinguir mayúsculas.
        """
        ...

    def update(self, project: Project) -> None:
        """Persiste los cambios de un proyecto existente."""
        ...
