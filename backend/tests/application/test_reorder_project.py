"""Tests de los casos de uso ReorderProjectUp / ReorderProjectDown.

Ambos operan sobre `Project.position`, intercambiándolo con el del vecino
correspondiente en la lista completa de proyectos vivos.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.reorder_project import (
    ReorderProjectDown,
    ReorderProjectUp,
)
from lifeos.domain import Project, ProjectNotFound

from .fakes import InMemoryProjectRepository


def _seed_three_projects():
    repo = InMemoryProjectRepository()
    first = Project.create(name="First", position=0)
    second = Project.create(name="Second", position=1)
    third = Project.create(name="Third", position=2)
    for project in (first, second, third):
        repo.add(project)
    return repo, first, second, third


def test_reorder_up_swaps_with_the_previous_project():
    repo, first, second, third = _seed_three_projects()
    del third

    moved = ReorderProjectUp(repo).execute(second.id)

    assert moved.position == 0
    assert repo.get(first.id).position == 1
    assert repo.get(second.id).position == 0


def test_reorder_down_swaps_with_the_next_project():
    repo, first, second, third = _seed_three_projects()
    del first

    moved = ReorderProjectDown(repo).execute(second.id)

    assert moved.position == 2
    assert repo.get(second.id).position == 2
    assert repo.get(third.id).position == 1


def test_reorder_up_on_the_first_project_is_a_noop():
    repo, first, second, third = _seed_three_projects()
    del second, third

    moved = ReorderProjectUp(repo).execute(first.id)

    assert moved.position == 0


def test_reorder_down_on_the_last_project_is_a_noop():
    repo, first, second, third = _seed_three_projects()
    del first, second

    moved = ReorderProjectDown(repo).execute(third.id)

    assert moved.position == 2


@pytest.mark.parametrize("use_case_cls", [ReorderProjectUp, ReorderProjectDown])
def test_reorder_missing_project_raises(use_case_cls):
    with pytest.raises(ProjectNotFound):
        use_case_cls(InMemoryProjectRepository()).execute(uuid4())
