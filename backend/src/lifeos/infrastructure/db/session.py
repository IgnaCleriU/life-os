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


def configure_sqlite_pragmas(engine: Engine) -> None:
    """Fija los PRAGMA de SQLite que Life OS necesita, por conexión.

    - `foreign_keys=ON`: SQLite lo trae deshabilitado por defecto; sin esto, un
      `TaskModel.project_id` que no exista en `projects` se inserta sin error
      pese a la `foreign_key="projects.id"` declarada en el modelo.
    - `journal_mode=WAL`: con la DB compartida de la ADR 0007, el acceso
      concurrente es lo normal y no la excepción —la TUI, un servidor MCP
      lanzado por un agente y un proceso REST pueden tenerla abierta a la vez—.
      WAL deja que los lectores no bloqueen al escritor.
    - `busy_timeout`: sin él vale 0 y cualquier contención revienta al instante
      con `database is locked` en vez de esperar.

    En las bases en memoria de los tests, `journal_mode` sigue siendo `memory`:
    el PRAGMA no falla, simplemente no aplica.
    """

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def _make_engine():
    settings = get_settings()
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
    configure_sqlite_pragmas(engine)
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


def migrate_project_position_column(engine: Engine) -> None:
    """Migración ADR 0009: agrega `position` a `projects` si falta.

    `create_all()` no agrega columnas a tablas existentes, así que una DB
    creada antes de este cambio se queda sin `position` para siempre si
    nada más la agrega. Chequea `PRAGMA table_info` (vacío si la tabla
    todavía no existe — `create_all()`, llamado antes, ya la crea completa
    en ese caso) y, si la columna falta, la agrega y la rellena en el orden
    actual de `created_at`. Idempotente: si la columna ya está, no hace nada.

    La columna se agrega `NOT NULL DEFAULT 0` a propósito, no nullable: si
    el proceso muere entre el `ALTER TABLE` y el loop de relleno de abajo,
    ninguna fila queda con `position` en NULL (el guard de arriba sólo
    chequea que la columna exista, así que un relleno interrumpido nunca
    se reintenta). Con el tiebreaker por `created_at` que `_live()` agrega
    a su `ORDER BY`, un relleno que no llegó a correr igual ordena
    correctamente en las lecturas — no rompe nada, sólo no optimiza el
    valor real de `position` hasta la próxima escritura.
    """
    with engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(projects)"
            ).fetchall()
        }
        if not columns or "position" in columns:
            return

        connection.exec_driver_sql(
            "ALTER TABLE projects ADD COLUMN position INTEGER NOT NULL DEFAULT 0"
        )
        rows = connection.exec_driver_sql(
            "SELECT id FROM projects ORDER BY created_at"
        ).fetchall()
        for index, (project_id,) in enumerate(rows):
            connection.exec_driver_sql(
                "UPDATE projects SET position = ? WHERE id = ?",
                (index, project_id),
            )
        connection.commit()


def create_db_and_tables() -> None:
    """Crea las tablas declaradas en el metadata de SQLModel si no existen,
    y aplica las migraciones de esquema pendientes (ADR 0009).

    Idempotente — se puede llamar varias veces sin efecto adicional.
    """
    _ensure_sqlite_parent_dir()
    SQLModel.metadata.create_all(engine)
    migrate_project_position_column(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Entrega una `Session` ligada al engine del módulo."""
    with Session(engine) as session:
        yield session
