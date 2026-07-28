"""Caso de uso: borrar un Project.

El borrado es lógico, igual que en `DeleteTask`, y **no cascadea**: un proyecto
con tareas vivas no se borra. Cascadear obligaría a `RestoreProject` a recordar
exactamente qué tareas se llevó por delante —estado que la pila de deshacer de
la TUI ya guarda—, y dejaría tareas invisibles pero vivas si esa memoria se
pierde. Mover o borrar las tareas primero es explícito y reversible paso a paso.
"""

from __future__ import annotations

from uuid import UUID

from lifeos.application.ports import ProjectRepository, TaskRepository
from lifeos.domain import Project, ProjectNotEmpty, ProjectNotFound


class DeleteProject:
    """Borra lógicamente un proyecto que ya no tiene tareas vivas."""

    def __init__(
        self, project_repo: ProjectRepository, task_repo: TaskRepository
    ) -> None:
        self._project_repo = project_repo
        self._task_repo = task_repo

    def execute(self, project_id: UUID) -> Project:
        """Marca el proyecto como borrado; falla si todavía tiene tareas."""
        project = self._project_repo.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        if self._task_repo.list(project_id=project_id):
            raise ProjectNotEmpty(project_id)

        project.delete()
        self._project_repo.update(project)
        return project
