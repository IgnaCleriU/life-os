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


def test_move_to_reassigns_project():
    task = Task.create(project_id=uuid4(), title="Tarea")
    destino = uuid4()

    task.move_to(destino)

    assert task.project_id == destino


def test_describe_sets_and_clears_description():
    task = Task.create(project_id=uuid4(), title="Tarea", description="original")

    task.describe("nueva")
    assert task.description == "nueva"

    task.describe(None)
    assert task.description is None


def test_create_is_not_deleted():
    task = Task.create(project_id=uuid4(), title="Tarea")

    assert task.deleted_at is None
    assert task.is_deleted is False


def test_delete_marks_and_restore_clears():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.delete()
    assert task.is_deleted is True
    assert task.deleted_at.tzinfo is not None

    task.restore()
    assert task.is_deleted is False
    assert task.deleted_at is None


def test_delete_is_idempotent_and_keeps_original_timestamp():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.delete()
    primera_marca = task.deleted_at
    task.delete()

    assert task.deleted_at == primera_marca


def test_restore_is_idempotent():
    task = Task.create(project_id=uuid4(), title="Tarea")

    task.restore()

    assert task.deleted_at is None
