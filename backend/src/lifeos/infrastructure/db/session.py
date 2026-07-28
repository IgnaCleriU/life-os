"""Configuración del engine y la sesión de SQLite usados por los repositorios
concretos.

Módulo agnóstico de framework: no importa `fastapi` (eso es responsabilidad
de `adapters/rest/deps.py`, que envuelve `get_session()` para `Depends` en
un paso posterior del roadmap).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from lifeos.infrastructure.config import get_settings


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """Activa el enforcement de foreign keys en SQLite.

    SQLite lo trae deshabilitado por defecto por conexión; sin esto, un
    `TaskModel.project_id` que no exista en `projects` se inserta sin error
    pese a la `foreign_key="projects.id"` declarada en el modelo.
    """

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _make_engine():
    settings = get_settings()
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
    enable_sqlite_foreign_keys(engine)
    return engine


engine = _make_engine()


def _ensure_sqlite_parent_dir() -> None:
    """Crea el directorio de la DB si falta.

    Por defecto la DB vive bajo `XDG_DATA_HOME` (ver `config.py`), un
    directorio que puede no existir todavía en una máquina nueva; SQLite no
    lo crea solo y fallaría al abrir el archivo. No aplica a bases en
    memoria, donde `url.database` es `None`.
    """
    if engine.url.drivername.startswith("sqlite") and engine.url.database:
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)


def create_db_and_tables() -> None:
    """Crea las tablas declaradas en el metadata de SQLModel si no existen.

    Idempotente — se puede llamar varias veces sin efecto adicional.
    """
    _ensure_sqlite_parent_dir()
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Entrega una `Session` ligada al engine del módulo."""
    with Session(engine) as session:
        yield session
