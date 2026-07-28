"""Caso de uso: reactivar un Project (desarchivarlo o reabrirlo)."""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound


class ActivateProject:
    """Vuelve a poner un proyecto existente como activo."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        """Activa el proyecto y persiste el cambio; falla si no existe."""
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)

        project.activate()
        self._project_repo.update(project)
        return project
