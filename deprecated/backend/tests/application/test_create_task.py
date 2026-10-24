"""Tests del caso de uso CreateTask (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.create_task import CreateTask
from lifeos.domain import (
    DomainValidationError,
    Priority,
    Project,
    ProjectNotFound,
    TaskStatus,
)

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def _make_use_case():
    task_repo = InMemoryTaskRepository()
    project_repo = InMemoryProjectRepository()
    return CreateTask(task_repo, project_repo), task_repo, project_repo


def test_create_task_under_existing_project_persists_it():
    use_case, task_repo, project_repo = _make_use_case()
    project = Project.create(name="Life OS")
    project_repo.add(project)

    task = use_case.execute(
        project_id=project.id,
        title="Escribir tests",
        priority=Priority.HIGH,
    )

    assert task.project_id == project.id
    assert task.title == "Escribir tests"
    assert task.priority is Priority.HIGH
    assert task.status is TaskStatus.TODO
    assert task_repo.get(task.id) is task


def test_create_task_under_missing_project_raises():
    use_case, _, _ = _make_use_case()

    with pytest.raises(ProjectNotFound):
        use_case.execute(project_id=uuid4(), title="Tarea huérfana")


def test_create_task_with_empty_title_raises():
    use_case, _, project_repo = _make_use_case()
    project = Project.create(name="Life OS")
    project_repo.add(project)

    with pytest.raises(DomainValidationError):
        use_case.execute(project_id=project.id, title="   ")
