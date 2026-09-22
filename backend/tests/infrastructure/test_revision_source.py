"""Tests de `SQLiteRevisionSource`.

Lo que importa proteger es que la revisión cambie cuando escribe *otra*
conexión —otro proceso, en producción— y que no cambie si nadie escribe: es
lo que usa el overlay de Quickshell para decidir si vuelve a pedir datos.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from lifeos.domain import Project
from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)
from lifeos.infrastructure.db.revision import SQLiteRevisionSource
from lifeos.infrastructure.db.session import configure_sqlite_pragmas


@pytest.fixture
def file_engine(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'lifeos.db'}")
    configure_sqlite_pragmas(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _add_project(engine, name: str = "Casa") -> None:
    with Session(engine) as session:
        SQLiteProjectRepository(session).add(Project.create(name=name))
        session.commit()


def test_is_stable_without_writes(file_engine) -> None:
    source = SQLiteRevisionSource.for_engine(file_engine)

    assert source.current() == source.current()


def test_changes_after_a_write_through_the_engine(file_engine) -> None:
    source = SQLiteRevisionSource.for_engine(file_engine)
    before = source.current()

    _add_project(file_engine)

    assert source.current() != before


def test_changes_after_a_write_from_an_unrelated_connection(
    file_engine, tmp_path: Path
) -> None:
    """Simula otro proceso (p. ej. el servidor MCP) escribiendo el archivo."""
    source = SQLiteRevisionSource.for_engine(file_engine)
    before = source.current()

    other = sqlite3.connect(tmp_path / "lifeos.db")
    other.execute("CREATE TABLE IF NOT EXISTS scratch (x INTEGER)")
    other.execute("INSERT INTO scratch VALUES (1)")
    other.commit()
    other.close()

    assert source.current() != before


def test_in_memory_static_pool_sees_writes_on_the_shared_connection() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_pragmas(engine)
    SQLModel.metadata.create_all(engine)
    source = SQLiteRevisionSource.for_engine(engine)
    before = source.current()

    _add_project(engine)

    assert source.current() != before
