"""Tests de `SQLiteTaskRepository` contra una base SQLite real en memoria."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from lifeos.domain import Priority, Project, Task, TaskStatus
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.repositories.sqlite_task_repository import (
    SQLiteTaskRepository,
)


def _add_project(session) -> Project:
    """Crea y persiste un `Project`, requerido por el FK de `tasks.project_id`."""
    project = Project.create(name="Proyecto de prueba")
    SQLiteProjectRepository(session).add(project)
    return project


def test_add_get_and_list_by_project(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    other_project = _add_project(session)
    task = Task.create(project_id=project.id, title="Escribir tests")
    other = Task.create(project_id=other_project.id, title="Tarea de otro proyecto")

    repo.add(task)
    repo.add(other)

    assert repo.get(task.id) == task
    assert repo.list_by_project(project.id) == [task]


def test_get_missing_returns_none(session):
    repo = SQLiteTaskRepository(session)

    assert repo.get(uuid4()) is None


def test_list_by_project_empty(session):
    repo = SQLiteTaskRepository(session)

    assert repo.list_by_project(uuid4()) == []


def test_update_persists_status_change(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    task = Task.create(project_id=project.id, title="Tarea")
    repo.add(task)

    task.complete()
    repo.update(task)

    assert repo.get(task.id).status == TaskStatus.DONE


def test_update_persists_all_mutable_fields(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    task = Task.create(project_id=project.id, title="Tarea", priority=Priority.LOW)
    repo.add(task)

    task.rename("Tarea renombrada")
    task.change_priority(Priority.HIGH)
    task.reschedule(None)
    repo.update(task)

    reloaded = repo.get(task.id)
    assert reloaded.title == "Tarea renombrada"
    assert reloaded.priority == Priority.HIGH
    assert reloaded.due_date is None


def test_add_rejects_task_with_unknown_project_id(session):
    repo = SQLiteTaskRepository(session)
    task = Task.create(project_id=uuid4(), title="Tarea huérfana")

    with pytest.raises(IntegrityError):
        repo.add(task)
