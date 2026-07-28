"""Tests de `SQLiteProjectRepository` contra una base SQLite real en memoria."""

from uuid import uuid4

from lifeos.domain import Project, ProjectStatus
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)


def test_add_get_and_list(session):
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Life OS")

    repo.add(project)

    assert repo.get(project.id) == project
    assert repo.list() == [project]


def test_get_missing_returns_none(session):
    repo = SQLiteProjectRepository(session)

    assert repo.get(uuid4()) is None


def test_list_empty(session):
    repo = SQLiteProjectRepository(session)

    assert repo.list() == []


def test_deleted_project_is_invisible_to_get_and_list(session):
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Life OS")
    repo.add(project)

    project.delete()
    repo.update(project)

    assert repo.get(project.id) is None
    assert repo.list() == []


def test_deleted_project_is_reachable_with_include_deleted(session):
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Life OS")
    repo.add(project)
    project.delete()
    repo.update(project)

    recuperado = repo.get(project.id, include_deleted=True)

    assert recuperado is not None
    assert recuperado.is_deleted is True
    assert recuperado.deleted_at.tzinfo is not None


def test_update_persists_rename_and_status(session):
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Life OS")
    repo.add(project)

    project.rename("Life OS v2")
    project.archive()
    repo.update(project)

    reloaded = repo.get(project.id)
    assert reloaded.name == "Life OS v2"
    assert reloaded.status is ProjectStatus.ARCHIVED


def test_list_filters_by_status_and_text(session):
    repo = SQLiteProjectRepository(session)
    casa = Project.create(name="Casa de campo")
    finanzas = Project.create(name="Finanzas")
    finanzas.archive()
    repo.add(casa)
    repo.add(finanzas)

    assert [p.id for p in repo.list(statuses=[ProjectStatus.ARCHIVED])] == [finanzas.id]
    assert [p.id for p in repo.list(text="CASA")] == [casa.id]
