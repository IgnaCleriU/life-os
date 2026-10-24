"""Caso de uso: listar Project, con filtros opcionales.

Consulta los proyectos persistidos a través del puerto `ProjectRepository`, sin
atarse a ningún motor de persistencia concreto. Los filtros son opcionales y se
combinan con AND; sin ninguno, devuelve todos los proyectos vivos.
"""

from __future__ import annotations

from collections.abc import Sequence

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectStatus


class ListProjects:
    """Lista proyectos, opcionalmente filtrados."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(
        self,
        *,
        statuses: Sequence[ProjectStatus] | None = None,
        text: str | None = None,
    ) -> list[Project]:
        """Devuelve los proyectos que cumplen los filtros dados."""
        return self._project_repo.list(statuses=statuses, text=text)
