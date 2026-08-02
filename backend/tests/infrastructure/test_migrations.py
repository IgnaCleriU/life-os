"""Tests de la migración de esquema descrita en ADR 0009.

`SQLModel.metadata.create_all()` siempre crea la tabla `projects` completa,
`position` incluida - así que el fixture normal (`tests/infrastructure/
conftest.py`) nunca ejercita la rama "falta la columna". Estos tests
construyen a mano un esquema `projects` sin `position` (el que existía
antes de este cambio) para probar esa rama específicamente.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine
from sqlalchemy.pool import StaticPool

from lifeos.infrastructure.db.session import (
    configure_sqlite_pragmas,
    migrate_project_position_column,
)


def _engine_with_old_schema():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_pragmas(engine)
    metadata = MetaData()
    Table(
        "projects",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String),
        Column("description", String),
        Column("status", String),
        Column("created_at", DateTime),
        Column("deleted_at", DateTime),
    )
    metadata.create_all(engine)
    return engine, metadata.tables["projects"]


def _insert(engine, table, project_id: str, name: str, created_at: datetime) -> None:
    with engine.connect() as connection:
        connection.execute(
            table.insert(),
            [
                {
                    "id": project_id,
                    "name": name,
                    "description": None,
                    "status": "active",
                    "created_at": created_at,
                    "deleted_at": None,
                }
            ],
        )
        connection.commit()


def test_migration_adds_and_backfills_position_from_created_at_order():
    engine, table = _engine_with_old_schema()
    _insert(engine, table, "b", "Second", datetime(2026, 1, 2, tzinfo=timezone.utc))
    _insert(engine, table, "a", "First", datetime(2026, 1, 1, tzinfo=timezone.utc))

    migrate_project_position_column(engine)

    with engine.connect() as connection:
        rows = connection.exec_driver_sql(
            "SELECT id, position FROM projects ORDER BY position"
        ).fetchall()
    assert rows == [("a", 0), ("b", 1)]


def test_migration_is_idempotent():
    engine, table = _engine_with_old_schema()
    _insert(engine, table, "a", "First", datetime(2026, 1, 1, tzinfo=timezone.utc))

    migrate_project_position_column(engine)
    migrate_project_position_column(engine)  # must not raise or double-run

    with engine.connect() as connection:
        rows = connection.exec_driver_sql(
            "SELECT id, position FROM projects"
        ).fetchall()
    assert rows == [("a", 0)]


def test_migration_is_a_noop_when_the_table_does_not_exist_yet():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_pragmas(engine)

    migrate_project_position_column(engine)  # must not raise
