"""Caso de uso: actualizar los datos de un Project existente.

Actualización parcial: solo se modifican los campos provistos. Para
`description` se usa un centinela (`_UNSET`) que distingue "no tocar la
descripción" de "ponerla en None" (quitarla), igual que `UpdateTask`. Las
invariantes (nombre no vacío) las valida el dominio vía los métodos de
`Project`.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound

_UNSET = object()


class UpdateProject:
    """Actualiza parcialmente los datos de un proyecto existente."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None | object = _UNSET,
    ) -> Project:
        """Aplica solo los campos provistos y persiste el proyecto."""
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)

        if name is not None:
            project.rename(name)
        if description is not _UNSET:
            project.describe(description)  # type: ignore[arg-type]

        self._project_repo.update(project)
        return project
