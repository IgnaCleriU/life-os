"""Implementación SQLite del puerto `RevisionSource`.

Se apoya en `PRAGMA data_version`: sobre una conexión dada, su valor cambia
cada vez que *otra* conexión confirma un cambio en el archivo, sea del mismo
proceso o de otro (el servidor MCP, el CLI, la TUI). Por eso la fuente usa una
conexión propia y dedicada que nunca escribe: todas las escrituras de la app
pasan por el pool del engine, así que ninguna queda sin detectar, y no hace
falta tocar el esquema.

`data_version` no ve lo que confirma la *misma* conexión. Eso solo ocurre en
los tests, donde una base en memoria con `StaticPool` comparte una única
conexión; para cubrirlo el token incluye también `total_changes` de esa
conexión, que en producción queda fijo.
"""

from __future__ import annotations

import sqlite3
import threading
from functools import lru_cache

from sqlalchemy.engine import Engine


class SQLiteRevisionSource:
    """`RevisionSource` respaldado por `PRAGMA data_version`."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        # Los endpoints síncronos de FastAPI corren en un threadpool y esta
        # conexión es compartida: se serializa el acceso.
        self._lock = threading.Lock()

    @classmethod
    def for_database(cls, path: str) -> SQLiteRevisionSource:
        """Abre una conexión dedicada, en autocommit, al archivo dado."""
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        return cls(connection)

    @classmethod
    def for_engine(cls, engine: Engine) -> SQLiteRevisionSource:
        """Construye la fuente para la base a la que apunta `engine`.

        Con un archivo abre una conexión nueva. Con una base en memoria no
        hay otro camino que reutilizar la del engine (una conexión nueva
        vería otra base vacía), algo que solo tiene sentido con `StaticPool`.
        """
        database = engine.url.database
        if database and database != ":memory:":
            return cls.for_database(database)
        return cls(engine.raw_connection().driver_connection)

    def current(self) -> str:
        with self._lock:
            (data_version,) = self._connection.execute(
                "PRAGMA data_version"
            ).fetchone()
            return f"{data_version}.{self._connection.total_changes}"


@lru_cache
def get_revision_source() -> SQLiteRevisionSource:
    """Fuente de revisión única del proceso, ligada al engine de la app."""
    from lifeos.infrastructure.db.session import engine

    return SQLiteRevisionSource.for_engine(engine)
