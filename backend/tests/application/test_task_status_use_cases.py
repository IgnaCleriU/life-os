"""Tests de los casos de uso que transicionan el estado de una Task.

`StartTask` y `ReopenTask` acompañan al ya existente `CompleteTask` para cubrir
las tres transiciones del dominio; sin ellos no había forma de llegar a `doing`
desde ningún adaptador.
"""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.reopen_task import ReopenTask
from lifeos.application.use_cases.start_task import StartTask
from lifeos.domain import Task, TaskNotFound, TaskStatus

from .fakes import InMemoryTaskRepository


def _seed_task():
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    task_repo.add(task)
    return task_repo, task


def test_start_task_marks_doing_and_persists():
    task_repo, task = _seed_task()

    started = StartTask(task_repo).execute(task.id)

    assert started.status is TaskStatus.DOING
    assert task_repo.get(task.id).status is TaskStatus.DOING


def test_start_missing_task_raises():
    with pytest.raises(TaskNotFound):
        StartTask(InMemoryTaskRepository()).execute(uuid4())


def test_reopen_task_returns_to_todo_and_persists():
    task_repo, task = _seed_task()
    task.complete()
    task_repo.update(task)

    reopened = ReopenTask(task_repo).execute(task.id)

    assert reopened.status is TaskStatus.TODO
    assert task_repo.get(task.id).status is TaskStatus.TODO


def test_reopen_missing_task_raises():
    with pytest.raises(TaskNotFound):
        ReopenTask(InMemoryTaskRepository()).execute(uuid4())
