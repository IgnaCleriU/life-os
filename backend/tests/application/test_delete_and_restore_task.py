"""Tests de DeleteTask y RestoreTask (sin DB ni mocks, fakes en memoria).

Los dos casos de uso son el par que sostiene `dd` y `u` en la TUI: el borrado
es lógico justamente para que restaurar sea un cambio de campo y no una
reconstrucción de la entidad.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.delete_project import DeleteProject
from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.restore_task import RestoreTask
from lifeos.domain import Project, ProjectNotFound, Task, TaskNotFound

from .fakes import InMemoryProjectRepository, InMemoryTaskRepository


def _seed_task():
    project_repo = InMemoryProjectRepository()
    task_repo = InMemoryTaskRepository()
    project = Project.create(name="Proyecto")
    project_repo.add(project)
    task = Task.create(project_id=project.id, title="Tarea")
    task_repo.add(task)
    return project_repo, task_repo, task


def test_delete_marks_the_task_and_hides_it_from_listings():
    _, task_repo, task = _seed_task()

    deleted = DeleteTask(task_repo).execute(task.id)

    assert deleted.is_deleted is True
    assert task_repo.get(task.id) is None
    assert ListTasks(task_repo).execute(task.project_id) == []


def test_delete_missing_task_raises():
    with pytest.raises(TaskNotFound):
        DeleteTask(InMemoryTaskRepository()).execute(uuid4())


def test_restore_brings_the_task_back():
    project_repo, task_repo, task = _seed_task()
    DeleteTask(task_repo).execute(task.id)

    restored = RestoreTask(task_repo, project_repo).execute(task.id)

    assert restored.is_deleted is False
    assert task_repo.get(task.id) is not None
    assert ListTasks(task_repo).execute(task.project_id) == [restored]


def test_restore_missing_task_raises():
    with pytest.raises(TaskNotFound):
        RestoreTask(InMemoryTaskRepository(), InMemoryProjectRepository()).execute(
            uuid4()
        )


def test_restore_task_under_deleted_project_raises_and_leaves_it_deleted():
    """El caso que orfanaba tareas: borrar la única tarea de un proyecto
    permite borrar el proyecto (queda vacío); restaurar la tarea después no
    debe reflotarla colgada de un proyecto invisible."""
    project_repo, task_repo, task = _seed_task()
    DeleteTask(task_repo).execute(task.id)
    DeleteProject(project_repo, task_repo).execute(task.project_id)

    with pytest.raises(ProjectNotFound):
        RestoreTask(task_repo, project_repo).execute(task.id)

    assert task_repo.get(task.id) is None


def test_restore_task_under_missing_project_raises():
    project_repo = InMemoryProjectRepository()
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Huérfana")
    task_repo.add(task)
    DeleteTask(task_repo).execute(task.id)

    with pytest.raises(ProjectNotFound):
        RestoreTask(task_repo, project_repo).execute(task.id)


def test_delete_then_restore_preserves_every_field():
    project_repo, task_repo, task = _seed_task()
    task.complete()
    task_repo.update(task)

    DeleteTask(task_repo).execute(task.id)
    restored = RestoreTask(task_repo, project_repo).execute(task.id)

    assert restored.title == task.title
    assert restored.status == task.status
    assert restored.priority == task.priority
