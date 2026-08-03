"""Caso de uso: restaurar un Project borrado.

Es el inverso de `DeleteProject`. Como el borrado no cascadea, restaurar no
tiene que reconstruir nada salvo la posición: el proyecto vuelve a entrar
a la lista viva al final (`next_position()`), no a su `position` vieja -
esa posición pudo haber sido reutilizada por un proyecto creado mientras
este estaba borrado (`CreateProject` también usa `next_position()`, que
cuenta los borrados; sin esta reasignación, restaurar produciría dos
proyectos vivos con la misma `position`).
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound


class RestoreProject:
    """Deshace el borrado lógico de un proyecto."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        """Quita la marca de borrado, reasigna la posición y persiste el
        cambio."""
        project = self._project_repo.get(project_id, include_deleted=True)
        if project is None:
            raise ProjectNotFound(project_id)

        project.restore()
        project.position = self._project_repo.next_position()
        self._project_repo.update(project)
        return project
