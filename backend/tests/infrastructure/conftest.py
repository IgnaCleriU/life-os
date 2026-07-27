"""Fixtures compartidas para los tests de infrastructure.

Cada test recibe un engine SQLite en memoria aislado. `sqlite:///:memory:`
es por conexión (no por engine): sin `StaticPool`, una segunda `Session`
vería una base vacía. `StaticPool` fuerza que todas las sesiones del test
compartan la misma conexión.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.session import enable_sqlite_foreign_keys


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
