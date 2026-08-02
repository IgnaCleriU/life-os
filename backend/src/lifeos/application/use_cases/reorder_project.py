"""Casos de uso: reordenar un Project respecto de sus vecinos.

Nombrados "Reorder", no "Move" - `MoveTask` ya existe y significa "cambiar
de proyecto". Reusar "move" acá chocaría en significado con "cambiar de
posición en la lista", aunque las rutas/tools no choquen en nombre.

Ambas clases intercambian `position` con el vecino correspondiente en la
lista completa de proyectos vivos (`ProjectRepository.list()`, ya ordenada
por `position`); en el borde de la lista, no hacen nada - idempotentes,
igual que `CompleteTask`/`ArchiveProject`/etc.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project, ProjectNotFound


def _swap_with_neighbor(
    project_repo: ProjectRepository, project_id: UUID, *, offset: int
) -> Project:
    projects = project_repo.list()
    index = next(
        (i for i, project in enumerate(projects) if project.id == project_id), None
    )
    if index is None:
        raise ProjectNotFound(project_id)

    neighbor_index = index + offset
    project = projects[index]
    if 0 <= neighbor_index < len(projects):
        neighbor = projects[neighbor_index]
        project.position, neighbor.position = neighbor.position, project.position
        project_repo.update(project)
        project_repo.update(neighbor)
    return project


class ReorderProjectUp:
    """Intercambia la posición de un proyecto con la del anterior en la lista."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        return _swap_with_neighbor(self._project_repo, project_id, offset=-1)


class ReorderProjectDown:
    """Intercambia la posición de un proyecto con la del siguiente en la lista."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, project_id: UUID) -> Project:
        return _swap_with_neighbor(self._project_repo, project_id, offset=1)
