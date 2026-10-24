"""Tests del caso de uso UpdateProject (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.update_project import UpdateProject
from lifeos.domain import DomainValidationError, Project, ProjectNotFound

from .fakes import InMemoryProjectRepository


def _seed_project(**kwargs):
    project_repo = InMemoryProjectRepository()
    project = Project.create(name="Life OS", **kwargs)
    project_repo.add(project)
    return UpdateProject(project_repo), project_repo, project


def test_update_renames_and_persists():
    use_case, project_repo, project = _seed_project()

    updated = use_case.execute(project.id, name="Life OS v2")

    assert updated.name == "Life OS v2"
    assert project_repo.get(project.id).name == "Life OS v2"


def test_update_sets_description():
    use_case, _, project = _seed_project()

    updated = use_case.execute(project.id, description="Sistema operativo personal")

    assert updated.description == "Sistema operativo personal"


def test_update_clears_description_with_explicit_none():
    use_case, _, project = _seed_project(description="original")

    updated = use_case.execute(project.id, description=None)

    assert updated.description is None


def test_update_leaves_description_untouched_when_omitted():
    """El centinela `_UNSET` distingue "no tocar" de "poner en None"."""
    use_case, _, project = _seed_project(description="original")

    updated = use_case.execute(project.id, name="Otro nombre")

    assert updated.description == "original"


def test_update_with_empty_name_raises():
    use_case, _, project = _seed_project()

    with pytest.raises(DomainValidationError):
        use_case.execute(project.id, name="   ")


def test_update_missing_project_raises():
    with pytest.raises(ProjectNotFound):
        UpdateProject(InMemoryProjectRepository()).execute(uuid4(), name="X")
