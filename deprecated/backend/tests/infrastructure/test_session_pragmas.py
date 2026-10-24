"""Tests de los PRAGMA que `configure_sqlite_pragmas` fija por conexión.

Con la base compartida de la ADR 0007, varios procesos (TUI, MCP, REST) la
tienen abierta a la vez. WAL y `busy_timeout` son lo que hace que eso sea espera
en vez de `database is locked`, y la ADR 0008 los declara prerequisito del
adaptador de TUI.

Se usa una base en archivo, no en memoria: `journal_mode=WAL` no aplica a
`:memory:`, donde el modo sigue siendo `memory`.
"""

from __future__ import annotations

from sqlmodel import Session, create_engine, text

from lifeos.infrastructure.db.session import configure_sqlite_pragmas


def _engine_on(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pragmas.db'}",
        connect_args={"check_same_thread": False},
    )
    configure_sqlite_pragmas(engine)
    return engine


def test_wal_journal_mode_is_enabled(tmp_path):
    with Session(_engine_on(tmp_path)) as session:
        modo = session.exec(text("PRAGMA journal_mode")).one()[0]

    assert modo.lower() == "wal"


def test_busy_timeout_is_not_zero(tmp_path):
    """En cero, cualquier contención revienta al instante en vez de esperar."""
    with Session(_engine_on(tmp_path)) as session:
        timeout = session.exec(text("PRAGMA busy_timeout")).one()[0]

    assert timeout == 5000


def test_foreign_keys_stay_enabled(tmp_path):
    with Session(_engine_on(tmp_path)) as session:
        activadas = session.exec(text("PRAGMA foreign_keys")).one()[0]

    assert activadas == 1
