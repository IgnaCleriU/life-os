"""Tests unitarios de la entidad Task (Python puro, sin DB ni mocks)."""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from lifeos.domain import DomainValidationError, Priority, Task, TaskStatus


def test_create_uses_defaults():
    project_id = uuid4()

    task = Task.create(project_id=project_id, title="Escribir tests")

    assert isinstance(task.id, UUID)
    assert task.project_id == project_id
    assert task.title == "Escribir tests"
    assert task.status is TaskStatus.TODO
    assert task.priority is Priority.MEDIUM
    assert task.due_date is None
    assert task.description is None
    assert isinstance(task.created_at, datetime)
    assert task.created_at.tzinfo is not None


def test_create_normalizes_title():
    task = Task.create(project_id=uuid4(), title="  Tarea  ")

    assert task.title == "Tarea"


@pytest.mark.parametrize("invalid_title", ["", "   "])
def test_create_with_empty_title_raises(invalid_title):
    with pytest.raises(DomainValidationError):
        Task.create(project_id=uuid4(), title=invalid_title)


def test_state_transitions():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.start()
    assert task.status is TaskStatus.DOING

    task.complete()
    assert task.status is TaskStatus.DONE

    task.reopen()
    assert task.status is TaskStatus.TODO


def test_complete_is_idempotent():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.complete()
    task.complete()

    assert task.status is TaskStatus.DONE


def test_change_priority():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.change_priority(Priority.HIGH)

    assert task.priority is Priority.HIGH


def test_reschedule_sets_and_clears_due_date():
    task = Task.create(project_id=uuid4(), title="Tarea")
    due = date(2026, 8, 1)

    task.reschedule(due)
    assert task.due_date == due

    task.reschedule(None)
    assert task.due_date is None


def test_rename_with_empty_title_raises():
    task = Task.create(project_id=uuid4(), title="Tarea")

    with pytest.raises(DomainValidationError):
        task.rename("  ")
