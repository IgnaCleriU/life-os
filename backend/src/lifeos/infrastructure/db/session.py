"""Configuración del engine y la sesión de SQLite usados por los repositorios
concretos.

Módulo agnóstico de framework: no importa `fastapi` (eso es responsabilidad
de `adapters/rest/deps.py`, que envuelve `get_session()` para `Depends` en
un paso posterior del roadmap).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from lifeos.infrastructure.config import get_settings


def _make_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )


engine = _make_engine()


def create_db_and_tables() -> None:
    """Crea las tablas declaradas en el metadata de SQLModel si no existen.

    Idempotente — se puede llamar varias veces sin efecto adicional.
    """
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Entrega una `Session` ligada al engine del módulo."""
    with Session(engine) as session:
        yield session
