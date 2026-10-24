from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from lifeos.adapters.tui.keymap import KeymapRegistry, Scope


class HelpScreen(ModalScreen[None]):
    """?: every bound key, generated directly from the keymap registry and
    grouped by scope - the same single source of truth the palette and
    dispatch both read from, so the docs can never drift from the bindings.
    """

    BINDINGS: ClassVar[list[BindingType]] = []

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > VerticalScroll {
        width: 60%;
        height: 60%;
        border: solid $primary;
        background: $surface;
    }
    """

    def __init__(self, registry: KeymapRegistry) -> None:
        super().__init__()
        self._registry = registry

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(self._render_text(), id="help-content")

    def _render_text(self) -> str:
        lines: list[str] = []
        for scope in Scope:
            entries = [e for e in self._registry.all() if e.scope is scope]
            if not entries:
                continue
            lines.append(scope.value.upper())
            lines.extend(f"  {entry.key:<12} {entry.label}" for entry in entries)
            lines.append("")
        return "\n".join(lines).rstrip()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss()
