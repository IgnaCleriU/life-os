"""Fixtures compartidas para los tests de adapters/mcp.

Cada test recibe un servidor FastMCP con una DB SQLite en memoria aislada,
inyectada monkeypateando `deps.get_session` — análogo a como
`tests/adapters/rest/conftest.py` sobreescribe `get_db_session` vía
`app.dependency_overrides`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from lifeos.adapters.mcp import deps
from lifeos.adapters.mcp.server import create_server
from lifeos.infrastructure.db import models  # noqa: F401  (registra las tablas)
from lifeos.infrastructure.db.session import enable_sqlite_foreign_keys


@pytest.fixture
def mcp_server(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def _get_test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(deps, "get_session", _get_test_session)
    return create_server()


@pytest.fixture
def call_tool(mcp_server: Any) -> Callable[..., CallToolResult]:
    """Invoca una tool del `mcp_server` de este test y devuelve el resultado.

    Cada llamada abre su propia sesión cliente-servidor en memoria (vía el
    helper de test del SDK oficial) y ejecuta el `call_tool` de forma
    síncrona, para no tener que marcar cada test como `async`.
    """

    async def _call(
        name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        async with create_connected_server_and_client_session(mcp_server) as session:
            return await session.call_tool(name, arguments or {})

    def _call_sync(
        name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        return asyncio.run(_call(name, arguments))

    return _call_sync
