from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class ConfirmScreen(ModalScreen[bool]):
    """A generic yes/no confirmation modal, for any destructive action -
    used by `dd` (delete), not Projects/Tasks-specific in any way.
    """

    BINDINGS: ClassVar[list[BindingType]] = []

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen > Vertical {
        width: auto;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 1 2;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._message)
            yield Static("y / enter: yes    n / esc: no")

    async def on_key(self, event: events.Key) -> None:
        if event.key in ("y", "enter"):
            event.prevent_default()
            event.stop()
            self.dismiss(True)
        elif event.key in ("n", "escape"):
            event.prevent_default()
            event.stop()
            self.dismiss(False)
