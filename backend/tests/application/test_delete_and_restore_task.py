"""Tests de DeleteTask y RestoreTask (sin DB ni mocks, fakes en memoria).

Los dos casos de uso son el par que sostiene `dd` y `u` en la TUI: el borrado
es lógico justamente para que restaurar sea un cambio de campo y no una
reconstrucción de la entidad.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.list_tasks import ListTasks
from lifeos.application.use_cases.restore_task import RestoreTask
from lifeos.domain import Task, TaskNotFound

from .fakes import InMemoryTaskRepository


def _seed_task():
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    task_repo.add(task)
    return task_repo, task


def test_delete_marks_the_task_and_hides_it_from_listings():
    task_repo, task = _seed_task()

    deleted = DeleteTask(task_repo).execute(task.id)

    assert deleted.is_deleted is True
    assert task_repo.get(task.id) is None
    assert ListTasks(task_repo).execute(task.project_id) == []


def test_delete_missing_task_raises():
    with pytest.raises(TaskNotFound):
        DeleteTask(InMemoryTaskRepository()).execute(uuid4())


def test_restore_brings_the_task_back():
    task_repo, task = _seed_task()
    DeleteTask(task_repo).execute(task.id)

    restored = RestoreTask(task_repo).execute(task.id)

    assert restored.is_deleted is False
    assert task_repo.get(task.id) is not None
    assert ListTasks(task_repo).execute(task.project_id) == [restored]


def test_restore_missing_task_raises():
    with pytest.raises(TaskNotFound):
        RestoreTask(InMemoryTaskRepository()).execute(uuid4())


def test_delete_then_restore_preserves_every_field():
    task_repo, task = _seed_task()
    task.complete()
    task_repo.update(task)

    DeleteTask(task_repo).execute(task.id)
    restored = RestoreTask(task_repo).execute(task.id)

    assert restored.title == task.title
    assert restored.status == task.status
    assert restored.priority == task.priority
