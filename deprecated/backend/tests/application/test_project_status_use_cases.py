"""Tests de los casos de uso que transicionan el estado de un Project.

`CompleteProject`, `ArchiveProject` y `ActivateProject` exponen métodos que el
dominio ya tenía pero que ningún caso de uso alcanzaba.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.activate_project import ActivateProject
from lifeos.application.use_cases.archive_project import ArchiveProject
from lifeos.application.use_cases.complete_project import CompleteProject
from lifeos.domain import Project, ProjectNotFound, ProjectStatus

from .fakes import InMemoryProjectRepository


def _seed_project():
    project_repo = InMemoryProjectRepository()
    project = Project.create(name="Life OS")
    project_repo.add(project)
    return project_repo, project


def test_complete_project_marks_completed_and_persists():
    project_repo, project = _seed_project()

    completed = CompleteProject(project_repo).execute(project.id)

    assert completed.status is ProjectStatus.COMPLETED
    assert project_repo.get(project.id).status is ProjectStatus.COMPLETED


def test_archive_project_marks_archived_and_persists():
    project_repo, project = _seed_project()

    archived = ArchiveProject(project_repo).execute(project.id)

    assert archived.status is ProjectStatus.ARCHIVED
    assert project_repo.get(project.id).status is ProjectStatus.ARCHIVED


def test_activate_project_returns_to_active_and_persists():
    project_repo, project = _seed_project()
    ArchiveProject(project_repo).execute(project.id)

    activated = ActivateProject(project_repo).execute(project.id)

    assert activated.status is ProjectStatus.ACTIVE
    assert project_repo.get(project.id).status is ProjectStatus.ACTIVE


@pytest.mark.parametrize(
    "use_case_cls", [CompleteProject, ArchiveProject, ActivateProject]
)
def test_transition_on_missing_project_raises(use_case_cls):
    with pytest.raises(ProjectNotFound):
        use_case_cls(InMemoryProjectRepository()).execute(uuid4())
