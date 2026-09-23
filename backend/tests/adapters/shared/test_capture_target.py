"""Tests de la resolución del proyecto destino de una captura.

Con callables simples en lugar de casos de uso: el módulo no conoce la capa
de aplicación, solo el contrato "texto -> proyectos".
"""

from __future__ import annotations

import pytest

from lifeos.adapters.shared.capture_target import (
    INBOX_PROJECT_NAME,
    AmbiguousProjectName,
    ProjectNameNotFound,
    find_projects_by_name,
    resolve_capture_target,
    resolve_project_by_name,
)
from lifeos.domain import Project


class _Projects:
    def __init__(self, *names: str) -> None:
        self.items = [Project.create(name=n) for n in names]

    def list(self) -> list[Project]:
        return list(self.items)

    def create(self, name: str) -> Project:
        project = Project.create(name=name)
        self.items.append(project)
        return project


def test_find_matches_exactly_ignoring_case_and_padding() -> None:
    projects = _Projects("Casa", "Casa de playa", "casa").items

    matches = find_projects_by_name(projects, "  CASA ")

    assert [p.name for p in matches] == ["Casa", "casa"]


def test_resolve_by_name_returns_the_single_match() -> None:
    projects = _Projects("Casa", "Casa de playa")

    assert resolve_project_by_name("casa", list_projects=projects.list).name == "Casa"


def test_resolve_by_name_unknown_raises() -> None:
    with pytest.raises(ProjectNameNotFound):
        resolve_project_by_name("nada", list_projects=_Projects("Casa").list)


def test_resolve_by_name_ambiguous_raises_with_candidates() -> None:
    projects = _Projects("Casa", "casa")

    with pytest.raises(AmbiguousProjectName) as exc_info:
        resolve_project_by_name("Casa", list_projects=projects.list)

    assert set(exc_info.value.candidates) == {p.id for p in projects.items}


def test_explicit_name_wins_over_default() -> None:
    projects = _Projects("Casa", "Finanzas")

    target = resolve_capture_target(
        "finanzas", list_projects=projects.list, default=lambda: projects.items[0]
    )

    assert target.name == "Finanzas"


def test_default_is_used_without_a_name() -> None:
    projects = _Projects("Casa")

    target = resolve_capture_target(
        None, list_projects=projects.list, default=lambda: projects.items[0]
    )

    assert target is projects.items[0]


def test_inbox_is_reused_when_it_exists() -> None:
    projects = _Projects(INBOX_PROJECT_NAME)

    target = resolve_capture_target(
        None, list_projects=projects.list, create_project=projects.create
    )

    assert target is projects.items[0]
    assert len(projects.items) == 1


def test_inbox_is_created_when_missing() -> None:
    projects = _Projects("Casa")

    target = resolve_capture_target(
        None, list_projects=projects.list, create_project=projects.create
    )

    assert target.name == INBOX_PROJECT_NAME
    assert len(projects.items) == 2


def test_missing_inbox_without_create_raises() -> None:
    with pytest.raises(ProjectNameNotFound):
        resolve_capture_target(None, list_projects=_Projects("Casa").list)


def test_resolve_by_name_folds_non_ascii_case() -> None:
    """`#árbol` encuentra "Árbol": SQLite `LIKE` no pliega no-ASCII, casefold sí."""
    projects = _Projects("Árbol genealógico", "Árbol")

    assert resolve_project_by_name("ÁRBOL", list_projects=projects.list).name == "Árbol"
