"""Tests de `SQLiteProjectRepository` contra una base SQLite real en memoria."""

from uuid import uuid4

from lifeos.domain import Project
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)


def test_add_get_and_list_all(session):
    repo = SQLiteProjectRepository(session)
    project = Project.create(name="Life OS")

    repo.add(project)

    assert repo.get(project.id) == project
    assert repo.list_all() == [project]


def test_get_missing_returns_none(session):
    repo = SQLiteProjectRepository(session)

    assert repo.get(uuid4()) is None


def test_list_all_empty(session):
    repo = SQLiteProjectRepository(session)

    assert repo.list_all() == []
