"""Shared fixtures for backend/tests/adapters/tui - mirrors
tests/adapters/cli/conftest.py's in-memory-SQLite pattern, but for the TUI's
own deps.py (no CliRunner here, there's no Typer app to invoke).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from lifeos.adapters.tui import deps
from lifeos.infrastructure.db import models  # noqa: F401  (registers the tables)
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
    """Direct session over the test engine, for seeding/asserting data."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def tui_env(engine, monkeypatch: pytest.MonkeyPatch):
    """Monkeypatches `deps.get_session` to use the test engine."""

    @contextmanager
    def _get_test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(deps, "get_session", _get_test_session)
    return engine
