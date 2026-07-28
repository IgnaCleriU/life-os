"""Caso de uso: marcar un Project como finalizado."""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound


class CompleteProject:
    """Marca un proyecto existente como finalizado."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        """Completa el proyecto y persiste el cambio; falla si no existe."""
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)

        project.complete()
        self._project_repo.update(project)
        return project
