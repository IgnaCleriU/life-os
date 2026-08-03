"""Tests del caso de uso CreateProject (con repositorio fake, sin mocks)."""

from uuid import UUID

import pytest

from lifeos.application.use_cases.create_project import CreateProject
from lifeos.domain import DomainValidationError, ProjectStatus

from .fakes import InMemoryProjectRepository


def test_create_persists_and_returns_project():
    repo = InMemoryProjectRepository()
    use_case = CreateProject(repo)

    project = use_case.execute(name="Life OS", description="Sistema operativo personal")

    assert isinstance(project.id, UUID)
    assert project.name == "Life OS"
    assert project.description == "Sistema operativo personal"
    assert project.status is ProjectStatus.ACTIVE
    assert repo.get(project.id) is project


def test_create_without_description_defaults_to_none():
    repo = InMemoryProjectRepository()
    use_case = CreateProject(repo)

    project = use_case.execute(name="Sin descripción")

    assert project.description is None


def test_create_assigns_sequential_positions():
    repo = InMemoryProjectRepository()
    use_case = CreateProject(repo)

    first = use_case.execute(name="First")
    second = use_case.execute(name="Second")
    third = use_case.execute(name="Third")

    assert (first.position, second.position, third.position) == (0, 1, 2)


@pytest.mark.parametrize("invalid_name", ["", "   "])
def test_create_with_empty_name_raises(invalid_name):
    repo = InMemoryProjectRepository()
    use_case = CreateProject(repo)

    with pytest.raises(DomainValidationError):
        use_case.execute(name=invalid_name)

    assert repo.list() == []
