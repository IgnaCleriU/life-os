"""Fixtures compartidas para los tests de adapters/rest.

Cada test recibe un `TestClient` con una DB SQLite en memoria aislada,
inyectada vía `app.dependency_overrides` en el punto único `get_db_session`
del que cuelga toda la cadena de repositorios/casos de uso.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from lifeos.adapters.rest.deps import get_db_session
from lifeos.adapters.rest.main import app
from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.session import enable_sqlite_foreign_keys


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    SQLModel.metadata.create_all(engine)

    def _get_test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = _get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
