"""Tests del caso de uso GetTask (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.delete_task import DeleteTask
from lifeos.application.use_cases.get_task import GetTask
from lifeos.domain import Task, TaskNotFound

from .fakes import InMemoryTaskRepository


def test_get_returns_the_task():
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    task_repo.add(task)

    assert GetTask(task_repo).execute(task.id) is task


def test_get_missing_task_raises():
    with pytest.raises(TaskNotFound):
        GetTask(InMemoryTaskRepository()).execute(uuid4())


def test_get_deleted_task_raises():
    """Una tarea borrada no existe para quien la busque por id."""
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    task_repo.add(task)
    DeleteTask(task_repo).execute(task.id)

    with pytest.raises(TaskNotFound):
        GetTask(task_repo).execute(task.id)
