"""Tests de DeleteProject y RestoreProject (sin DB ni mocks, fakes en memoria).

El borrado de proyectos no cascadea: un proyecto con tareas vivas no se borra.
La alternativa —arrastrar las tareas— obligaría a `RestoreProject` a recordar
cuáles se llevó, y dejaría tareas vivas colgando de un proyecto invisible si esa
memoria se pierde.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.create_project import CreateProject
from lifeos.application.use_cases.delete_project import DeleteProject
from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.list_projects import ListProjects
from lifeos.application.use_cases.restore_project import RestoreProject
from lifeos.domain import Project, ProjectNotEmpty, ProjectNotFound, Task

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def _seed():
    project_repo = InMemoryProjectRepository()
    task_repo = InMemoryTaskRepository()
    project = Project.create(name="Life OS")
    project_repo.add(project)
    return project_repo, task_repo, project


def test_delete_empty_project_marks_it_and_hides_it_from_listings():
    project_repo, task_repo, project = _seed()

    deleted = DeleteProject(project_repo, task_repo).execute(project.id)

    assert deleted.is_deleted is True
    assert project_repo.get(project.id) is None
    assert ListProjects(project_repo).execute() == []


def test_delete_project_with_live_tasks_raises_and_changes_nothing():
    project_repo, task_repo, project = _seed()
    task_repo.add(Task.create(project_id=project.id, title="Tarea viva"))

    with pytest.raises(ProjectNotEmpty):
        DeleteProject(project_repo, task_repo).execute(project.id)

    assert project_repo.get(project.id) is not None


def test_delete_project_succeeds_once_its_tasks_are_deleted():
    """Una tarea borrada ya no cuenta como viva."""
    project_repo, task_repo, project = _seed()
    task = Task.create(project_id=project.id, title="Tarea")
    task_repo.add(task)
    DeleteTask(task_repo).execute(task.id)

    deleted = DeleteProject(project_repo, task_repo).execute(project.id)

    assert deleted.is_deleted is True


def test_delete_project_ignores_tasks_of_other_projects():
    project_repo, task_repo, project = _seed()
    task_repo.add(Task.create(project_id=uuid4(), title="Tarea ajena"))

    assert DeleteProject(project_repo, task_repo).execute(project.id).is_deleted


def test_delete_missing_project_raises():
    with pytest.raises(ProjectNotFound):
        DeleteProject(
            InMemoryProjectRepository(), InMemoryTaskRepository()
        ).execute(uuid4())


def test_restore_brings_the_project_back():
    project_repo, task_repo, project = _seed()
    DeleteProject(project_repo, task_repo).execute(project.id)

    restored = RestoreProject(project_repo).execute(project.id)

    assert restored.is_deleted is False
    assert ListProjects(project_repo).execute() == [restored]


def test_restore_missing_project_raises():
    with pytest.raises(ProjectNotFound):
        RestoreProject(InMemoryProjectRepository()).execute(uuid4())


def test_restore_never_collides_position_with_a_project_created_after_the_delete():
    """A(0), B(1); delete B; create C (would land at position 1 if computed
    only from live projects); restore B - B and C must not both end up at
    position 1, or the swap in ReorderProjectUp/Down would be a permanent
    no-op between them."""
    project_repo = InMemoryProjectRepository()
    task_repo = InMemoryTaskRepository()
    a = Project.create(name="A", position=0)
    b = Project.create(name="B", position=1)
    project_repo.add(a)
    project_repo.add(b)

    DeleteProject(project_repo, task_repo).execute(b.id)
    c = CreateProject(project_repo).execute(name="C")
    restored_b = RestoreProject(project_repo).execute(b.id)

    live_positions = [p.position for p in ListProjects(project_repo).execute()]
    assert len(live_positions) == len(set(live_positions))
    assert restored_b.position != c.position
