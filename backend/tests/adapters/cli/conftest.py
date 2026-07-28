"""Fixtures compartidas para los tests de adapters/cli.

Cada test recibe una DB SQLite en memoria aislada, inyectada monkeypateando
`deps.get_session` — análogo a `tests/adapters/mcp/conftest.py`, pero para
el adaptador CLI (typer): en vez de un servidor FastMCP, exponemos un
`CliRunner` para invocar el `app` de typer directamente en memoria.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from typer.testing import CliRunner

from lifeos.adapters.cli import deps
from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.session import configure_sqlite_pragmas


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configure_sqlite_pragmas(test_engine)
    SQLModel.metadata.create_all(test_engine)
    return test_engine


@pytest.fixture
def db_session(engine) -> Iterator[Session]:
    """Sesión directa sobre el engine de test, para sembrar/verificar datos."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def cli_env(engine, monkeypatch: pytest.MonkeyPatch):
    """Monkeypatchea `deps.get_session` para que use el engine de test."""

    from contextlib import contextmanager

    @contextmanager
    def _get_test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(deps, "get_session", _get_test_session)
    return engine


@pytest.fixture
def runner(cli_env) -> CliRunner:
    """CliRunner de typer con la DB de test ya inyectada vía `cli_env`."""
    return CliRunner()
