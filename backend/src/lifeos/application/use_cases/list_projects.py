"""Caso de uso: listar los Project existentes.

Consulta todos los proyectos persistidos a través del puerto
`ProjectRepository`, sin atarse a ningún motor de persistencia concreto.
"""

from __future__ import annotations

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project


class ListProjects:
    """Devuelve todos los `Project` persistidos."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self) -> list[Project]:
        """Devuelve todos los proyectos existentes."""
        return self._project_repo.list_all()
