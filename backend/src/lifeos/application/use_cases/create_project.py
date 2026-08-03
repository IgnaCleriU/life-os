"""Caso de uso: crear un Project.

Orquesta la creación de un proyecto nuevo delegando las invariantes al dominio
(`Project.create`) y persistiéndolo vía el puerto `ProjectRepository`.
"""

from __future__ import annotations

from lifeos.application.ports import ProjectRepository
from lifeos.domain import Project


class CreateProject:
    """Crea un `Project` y lo persiste a través del repositorio."""

    def __init__(self, project_repo: ProjectRepository) -> None:
        self._project_repo = project_repo

    def execute(self, name: str, description: str | None = None) -> Project:
        """Crea el proyecto, lo persiste y lo devuelve.

        La validación del nombre vive en el dominio: si es inválido,
        `Project.create` lanza `DomainValidationError`, que se propaga.

        `position` se calcula acá (no en el dominio, que no conoce a los
        demás proyectos) vía `ProjectRepository.next_position()`, para que
        el proyecto nuevo quede al final - y nunca choque con un proyecto
        borrado lógicamente que después se restaure (`next_position()`
        cuenta también los borrados; ver su docstring en el puerto).
        """
        position = self._project_repo.next_position()
        project = Project.create(name, description, position=position)
        self._project_repo.add(project)
        return project
