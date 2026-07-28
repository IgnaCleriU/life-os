"""Tests del caso de uso GetProject (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.delete_project import DeleteProject
from lifeos.application.use_cases.get_project import GetProject
from lifeos.domain import Project, ProjectNotFound

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def test_get_returns_the_project():
    project_repo = InMemoryProjectRepository()
    project = Project.create(name="Life OS")
    project_repo.add(project)

    assert GetProject(project_repo).execute(project.id) is project


def test_get_missing_project_raises():
    with pytest.raises(ProjectNotFound):
        GetProject(InMemoryProjectRepository()).execute(uuid4())


def test_get_deleted_project_raises():
    project_repo = InMemoryProjectRepository()
    project = Project.create(name="Life OS")
    project_repo.add(project)
    DeleteProject(project_repo, InMemoryTaskRepository()).execute(project.id)

    with pytest.raises(ProjectNotFound):
        GetProject(project_repo).execute(project.id)
