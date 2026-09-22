"""Resolución del proyecto destino de una captura quick-add.

El tokenizer (`quick_add.py`) solo extrae el `#nombre`; decidir en qué
proyecto cae la tarea es una regla aparte que CLI, TUI y REST deben aplicar
igual (spec 0002):

1. Un `#nombre` explícito gana. Se compara exacto, sin distinguir mayúsculas
   (`strip` + `casefold`). Cero coincidencias o más de una es un error: los
   nombres de proyecto no son únicos y elegir uno en silencio mandaría la
   tarea a donde no corresponde.
2. Si no, el proyecto por defecto que aporte el adapter (el seleccionado en
   el tablero, o `default_project_id` en REST).
3. Si no, el proyecto "inbox", creado al vuelo si todavía no existe.

Como el resto de `adapters/shared/`, no importa `application`: recibe los
casos de uso como callables, así cada adapter conserva su propio cableado.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from uuid import UUID

from lifeos.domain import Project

INBOX_PROJECT_NAME = "inbox"

ListProjectsByText = Callable[[str], list[Project]]
"""Devuelve los proyectos cuyo nombre contiene el texto (filtro amplio)."""


class ProjectNameNotFound(Exception):
    """No existe ningún proyecto con el nombre buscado."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No project found with name '{name}'")


class AmbiguousProjectName(Exception):
    """Más de un proyecto comparte el nombre buscado."""

    def __init__(self, name: str, candidates: list[UUID]) -> None:
        self.name = name
        self.candidates = candidates
        candidate_ids = ", ".join(str(candidate) for candidate in candidates)
        super().__init__(
            f"Multiple projects named '{name}' found: {candidate_ids}. "
            "Rename one or refer to it by id to disambiguate."
        )


def find_projects_by_name(projects: Iterable[Project], name: str) -> list[Project]:
    """Filtra `projects` a los que se llaman exactamente `name`."""
    target = name.strip().casefold()
    return [p for p in projects if p.name.strip().casefold() == target]


def resolve_project_by_name(name: str, *, list_projects: ListProjectsByText) -> Project:
    """Devuelve el único proyecto llamado `name`; falla si hay 0 o más de 1."""
    matches = find_projects_by_name(list_projects(name), name)
    if not matches:
        raise ProjectNameNotFound(name)
    if len(matches) > 1:
        raise AmbiguousProjectName(name, [p.id for p in matches])
    return matches[0]


def resolve_capture_target(
    project_name: str | None,
    *,
    list_projects: ListProjectsByText,
    default: Callable[[], Project] | None = None,
    create_project: Callable[[str], Project] | None = None,
) -> Project:
    """Aplica las tres reglas del docstring del módulo, en orden.

    Sin `create_project`, un inbox inexistente es `ProjectNameNotFound` en
    vez de crearse (útil para quien no debe escribir).
    """
    if project_name is not None:
        return resolve_project_by_name(project_name, list_projects=list_projects)
    if default is not None:
        return default()
    try:
        return resolve_project_by_name(
            INBOX_PROJECT_NAME, list_projects=list_projects
        )
    except ProjectNameNotFound:
        if create_project is None:
            raise
        return create_project(INBOX_PROJECT_NAME)
