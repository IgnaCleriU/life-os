"""Tests del caso de uso UpdateTask (sin DB ni mocks, fakes en memoria)."""

from datetime import date
from uuid import uuid4

import pytest

from lifeos.application.use_cases.update_task import UpdateTask
from lifeos.domain import Priority, Task, TaskNotFound

from .fakes import InMemoryTaskRepository


def _seed_task(**kwargs):
    task_repo = InMemoryTaskRepository()
    task = Task.create(project_id=uuid4(), title="Tarea", **kwargs)
    task_repo.add(task)
    return UpdateTask(task_repo), task_repo, task


def test_update_title_and_priority():
    use_case, task_repo, task = _seed_task()

    updated = use_case.execute(task.id, title="Nuevo título", priority=Priority.HIGH)

    assert updated.title == "Nuevo título"
    assert updated.priority is Priority.HIGH
    assert task_repo.get(task.id).title == "Nuevo título"


def test_update_reschedule_sets_due_date():
    use_case, _, task = _seed_task()
    due = date(2026, 8, 1)

    updated = use_case.execute(task.id, due_date=due)

    assert updated.due_date == due


def test_update_reschedule_clears_due_date_with_explicit_none():
    use_case, _, task = _seed_task(due_date=date(2026, 8, 1))

    updated = use_case.execute(task.id, due_date=None)

    assert updated.due_date is None


def test_update_without_due_date_leaves_it_unchanged():
    due = date(2026, 8, 1)
    use_case, _, task = _seed_task(due_date=due)

    updated = use_case.execute(task.id, title="Solo título")

    assert updated.due_date == due


def test_update_missing_task_raises():
    use_case, _, _ = _seed_task()

    with pytest.raises(TaskNotFound):
        use_case.execute(uuid4(), title="No existe")
