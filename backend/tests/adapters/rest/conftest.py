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

from lifeos.adapters.rest.deps import get_db_session, get_revision_source
from lifeos.adapters.rest.main import create_app
from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.revision import SQLiteRevisionSource
from lifeos.infrastructure.db.session import configure_sqlite_pragmas


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_pragmas(engine)
    SQLModel.metadata.create_all(engine)
    return engine


def make_client(engine, **app_kwargs) -> TestClient:
    """`TestClient` sobre una app nueva cuya sesión de DB apunta a `engine`."""
    app = create_app(**app_kwargs)

    def _get_test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    revision_source = SQLiteRevisionSource.for_engine(engine)
    app.dependency_overrides[get_db_session] = _get_test_session
    app.dependency_overrides[get_revision_source] = lambda: revision_source
    return TestClient(app, base_url="http://127.0.0.1:8000")


@pytest.fixture
def client(engine) -> Iterator[TestClient]:
    """Cliente con la guardia local apagada: los tests de endpoints prueban
    el comportamiento de las rutas, no la auth (ver `test_auth.py`)."""
    with make_client(engine, auth_enabled=False) as test_client:
        yield test_client
