"""Caso de uso: obtener un Project por id."""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound


class GetProject:
    """Devuelve un proyecto existente por su id."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        """Devuelve el proyecto; falla si no existe o está borrado."""
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)

        return project
