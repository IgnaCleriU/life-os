"""Tests del caso de uso CompleteTask (sin DB ni mocks, fakes en memoria)."""

from uuid import uuid4

import pytest

from lifeos.application.use_cases.complete_task import CompleteTask
from lifeos.domain import Task, TaskNotFound, TaskStatus

from .fakes import InMemoryTaskRepository


def test_complete_task_marks_done_and_persists():
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea")
    task_repo.add(task)
    use_case = CompleteTask(task_repo)

    completed = use_case.execute(task.id)

    assert completed.status is TaskStatus.DONE
    assert task_repo.get(task.id).status is TaskStatus.DONE


def test_complete_missing_task_raises():
    use_case = CompleteTask(InMemoryTaskRepository())

    with pytest.raises(TaskNotFound):
        use_case.execute(uuid4())
