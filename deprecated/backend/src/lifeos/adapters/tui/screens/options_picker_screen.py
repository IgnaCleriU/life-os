from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option


class OptionsPickerScreen(ModalScreen[str | None]):
    """A generic "pick one of a few options" modal - used by the priority
    picker, status-filter menu, sort-order menu, and move-to-project picker.
    Not Projects/Tasks-specific: the caller supplies the title and the
    plain-string options.
    """

    BINDINGS: ClassVar[list[BindingType]] = []

    DEFAULT_CSS = """
    OptionsPickerScreen {
        align: center middle;
    }
    OptionsPickerScreen > Vertical {
        width: auto;
        height: auto;
        border: solid $primary;
        background: $surface;
    }
    """

    def __init__(self, title: str, options: list[str]) -> None:
        super().__init__()
        self._title = title
        self._option_labels = options

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._title)
            yield OptionList(
                *(Option(label, id=label) for label in self._option_labels),
                id="picker-options",
            )

    @property
    def options(self) -> OptionList:
        return self.query_one("#picker-options", OptionList)

    def on_mount(self) -> None:
        self.options.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.prompt))

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss(None)
