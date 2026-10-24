from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry


class PaletteScreen(ModalScreen[None]):
    """^k: a fuzzy-ish (plain substring, case-insensitive) command list
    generated directly from the keymap registry - no second list anywhere,
    so it structurally cannot drift from the actual bindings.
    """

    BINDINGS: ClassVar[list[BindingType]] = []

    DEFAULT_CSS = """
    PaletteScreen {
        align: center middle;
    }
    PaletteScreen > Vertical {
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
        with Vertical():
            yield Input(placeholder="Type a command...", id="palette-input")
            yield OptionList(id="palette-results")

    def on_mount(self) -> None:
        self._render_results(self._registry.all())
        self.query_one("#palette-input", Input).focus()

    @property
    def results(self) -> OptionList:
        return self.query_one("#palette-results", OptionList)

    def _render_results(self, entries: list[KeymapEntry]) -> None:
        results = self.results
        results.clear_options()
        for index, entry in enumerate(entries):
            results.add_option(Option(f"{entry.key}  {entry.label}", id=str(index)))
        self._visible_entries = entries
        if entries:
            results.highlighted = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        needle = event.value.casefold()
        matches = [e for e in self._registry.all() if needle in e.label.casefold()]
        self._render_results(matches)

    def _execute_highlighted(self) -> None:
        results = self.results
        if results.highlighted is None:
            return
        entry = self._visible_entries[results.highlighted]
        self.dismiss()
        entry.action()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._execute_highlighted()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._execute_highlighted()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss()
