"""Tests de `SQLiteTaskRepository` contra una base SQLite real en memoria."""

from datetime import date
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


def test_add_get_and_list_filtered_by_project(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    other_project = _add_project(session)
    task = Task.create(project_id=project.id, title="Escribir tests")
    other = Task.create(project_id=other_project.id, title="Tarea de otro proyecto")

    repo.add(task)
    repo.add(other)

    assert repo.get(task.id) == task
    assert repo.list(project_id=project.id) == [task]


def test_get_missing_returns_none(session):
    repo = SQLiteTaskRepository(session)

    assert repo.get(uuid4()) is None


def test_list_empty(session):
    repo = SQLiteTaskRepository(session)

    assert repo.list(project_id=uuid4()) == []


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


def test_deleted_task_is_invisible_to_get_and_list(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    task = Task.create(project_id=project.id, title="Tarea")
    repo.add(task)

    task.delete()
    repo.update(task)

    assert repo.get(task.id) is None
    assert repo.list(project_id=project.id) == []
    assert repo.list() == []


def test_deleted_task_is_reachable_with_include_deleted(session):
    """El único camino a una fila borrada, y lo usa sólo `RestoreTask`."""
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    task = Task.create(project_id=project.id, title="Tarea")
    repo.add(task)
    task.delete()
    repo.update(task)

    recuperada = repo.get(task.id, include_deleted=True)

    assert recuperada is not None
    assert recuperada.is_deleted is True
    assert recuperada.deleted_at.tzinfo is not None


def test_restore_makes_the_task_visible_again(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    task = Task.create(project_id=project.id, title="Tarea")
    repo.add(task)
    task.delete()
    repo.update(task)

    task.restore()
    repo.update(task)

    assert repo.get(task.id) is not None
    assert repo.list(project_id=project.id) == [task]


def test_list_filters_by_status(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    pendiente = Task.create(project_id=project.id, title="Pendiente")
    hecha = Task.create(project_id=project.id, title="Hecha")
    hecha.complete()
    repo.add(pendiente)
    repo.add(hecha)

    result = repo.list(statuses=[TaskStatus.DONE])

    assert [t.id for t in result] == [hecha.id]


def test_list_filters_by_due_before_and_excludes_undated(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    vencida = Task.create(
        project_id=project.id, title="Vencida", due_date=date(2026, 7, 1)
    )
    futura = Task.create(
        project_id=project.id, title="Futura", due_date=date(2026, 12, 1)
    )
    sin_fecha = Task.create(project_id=project.id, title="Sin fecha")
    for task in (vencida, futura, sin_fecha):
        repo.add(task)

    result = repo.list(due_before=date(2026, 7, 28))

    assert [t.id for t in result] == [vencida.id]


def test_list_filters_by_text_case_insensitively(session):
    repo = SQLiteTaskRepository(session)
    project = _add_project(session)
    match = Task.create(project_id=project.id, title="Pagar EXPENSAS")
    otra = Task.create(project_id=project.id, title="Otra cosa")
    repo.add(match)
    repo.add(otra)

    result = repo.list(text="expensas")

    assert [t.id for t in result] == [match.id]


def test_update_persists_move_to_another_project(session):
    repo = SQLiteTaskRepository(session)
    origen = _add_project(session)
    destino = _add_project(session)
    task = Task.create(project_id=origen.id, title="Tarea")
    repo.add(task)

    task.move_to(destino.id)
    repo.update(task)

    assert repo.get(task.id).project_id == destino.id
    assert repo.list(project_id=origen.id) == []
