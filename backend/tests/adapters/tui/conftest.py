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
from lifeos.adapters.tui.undo import UndoStack
from lifeos.infrastructure.db import models  # noqa: F401  (registers the tables)
from lifeos.infrastructure.db.session import configure_sqlite_pragmas


class FakeShell:
    """Just enough of ShellScreen's public surface for a module's own
    actions to call, without mounting a real Textual App - full keypress-
    driven wiring is covered separately in test_app_wiring.py."""

    def __init__(self) -> None:
        self.undo_stack = UndoStack()
        self.reload_count = 0
        self.errors: list[str] = []
        self.current_context_item = None
        self.current_collection_item = None
        self.clipboard: list[str] = []
        self.selected_ids: set[str] = set()
        self._pending_commit = None
        self._pending_confirm = None
        self._pending_pick: tuple[list[str], object] | None = None

    def copy_to_clipboard(self, text: str) -> None:
        self.clipboard.append(text)

    def enter_select_mode(self) -> None:
        pass

    def toggle_selection(self, item_id: str) -> None:
        if item_id in self.selected_ids:
            self.selected_ids.discard(item_id)
        else:
            self.selected_ids.add(item_id)

    def prompt_insert(self, *, placeholder: str = "", on_commit) -> None:  # noqa: ANN001
        self._pending_commit = on_commit

    def commit_pending_prompt(self, text: str) -> None:
        assert self._pending_commit is not None
        commit, self._pending_commit = self._pending_commit, None
        commit(text)

    def confirm(self, message: str, *, on_yes) -> None:  # noqa: ANN001
        self._pending_confirm = on_yes

    def confirm_yes(self) -> None:
        assert self._pending_confirm is not None
        on_yes, self._pending_confirm = self._pending_confirm, None
        on_yes()

    def pick_option(self, title: str, options: list[str], *, on_select) -> None:  # noqa: ANN001
        self._pending_pick = (options, on_select)

    def pick(self, option: str) -> None:
        assert self._pending_pick is not None
        options, on_select = self._pending_pick
        assert option in options
        self._pending_pick = None
        on_select(option)

    def action_reload(self) -> None:
        self.reload_count += 1

    def show_error(self, message: str) -> None:
        self.errors.append(message)


@pytest.fixture
def fake_shell() -> FakeShell:
    return FakeShell()


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
