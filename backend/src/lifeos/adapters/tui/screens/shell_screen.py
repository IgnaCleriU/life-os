from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import OptionList

from lifeos.adapters.tui.dispatch import KeySequenceBuffer
from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope
from lifeos.adapters.tui.modes import Mode
from lifeos.adapters.tui.module import TuiModule
from lifeos.adapters.tui.widgets.panes import CollectionPane, ContextPane, DetailPane
from lifeos.adapters.tui.widgets.status_bar import StatusBar

_PANE_IDS = ["context-pane", "collection-pane", "detail-pane"]


class ShellScreen(Screen[None]):
    """The 3-pane + status-bar shell. Composes panes and a status bar,
    dispatches every keypress through a KeymapRegistry via KeySequenceBuffer
    (ADR 0008's single dispatch path - no widget here keeps its own Textual
    BINDINGS), and keeps panes in sync with the module's own selection state.

    Builds its own registry from its global navigation entries plus
    `module.keymap_entries()`. A future ShellApp merges in nothing further -
    this screen already owns the full registry it dispatches against.
    """

    DEFAULT_CSS = """
    ShellScreen {
        layout: vertical;
    }
    ShellScreen > Horizontal {
        height: 1fr;
    }
    ContextPane, CollectionPane, DetailPane {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }
    StatusBar {
        dock: bottom;
        height: 1;
    }
    """

    def __init__(self, module: TuiModule, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.module = module
        entries = [*self._global_entries(), *module.keymap_entries()]
        self.registry = KeymapRegistry(entries)
        self.buffer = KeySequenceBuffer(self.registry)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ContextPane(id="context-pane")
            yield CollectionPane(id="collection-pane")
            yield DetailPane(id="detail-pane")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._refresh_context_pane()
        self.query_one("#context-pane", ContextPane).focus()
        self._refresh_status_bar()

    # --- global keymap entries (this screen's own bound methods as actions) --

    def _global_entries(self) -> list[KeymapEntry]:
        focus_prev = self.action_focus_previous_pane
        focus_next = self.action_focus_next_pane
        return [
            KeymapEntry(Scope.GLOBAL, "h", "focus previous pane", focus_prev),
            KeymapEntry(Scope.GLOBAL, "l", "focus next pane", focus_next),
            KeymapEntry(Scope.GLOBAL, "shift+tab", "focus previous pane", focus_prev),
            KeymapEntry(Scope.GLOBAL, "tab", "focus next pane", focus_next),
            KeymapEntry(Scope.GLOBAL, "j", "cursor down", self.action_cursor_down),
            KeymapEntry(Scope.GLOBAL, "k", "cursor up", self.action_cursor_up),
            KeymapEntry(Scope.GLOBAL, "gg", "first item", self.action_first),
            KeymapEntry(Scope.GLOBAL, "G", "last item", self.action_last),
            KeymapEntry(
                Scope.GLOBAL, "ctrl+d", "half-page down", self.action_page_down
            ),
            KeymapEntry(Scope.GLOBAL, "ctrl+u", "half-page up", self.action_page_up),
        ]

    # --- scope tracking (derived from focus, not separately maintained) -----

    @property
    def current_scope(self) -> Scope:
        focused = self.focused
        if isinstance(focused, ContextPane):
            return Scope.CONTEXT
        if isinstance(focused, CollectionPane):
            return Scope.COLLECTION
        if isinstance(focused, DetailPane):
            return Scope.DETAIL
        return Scope.GLOBAL

    def _pane_index(self) -> int:
        focused = self.focused
        for index, pane_id in enumerate(_PANE_IDS):
            if focused is self.query_one(f"#{pane_id}"):
                return index
        return 0

    # --- dispatch -------------------------------------------------------------

    async def on_key(self, event: events.Key) -> None:
        result = self.buffer.feed(self.current_scope, event.key)
        if result.kind == "no_match":
            return
        event.prevent_default()
        event.stop()
        if result.kind == "matched" and result.entry is not None:
            result.entry.action()

    # --- global actions ---------------------------------------------------

    def action_focus_next_pane(self) -> None:
        index = min(self._pane_index() + 1, len(_PANE_IDS) - 1)
        self.query_one(f"#{_PANE_IDS[index]}").focus()

    def action_focus_previous_pane(self) -> None:
        index = max(self._pane_index() - 1, 0)
        self.query_one(f"#{_PANE_IDS[index]}").focus()

    def action_cursor_down(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_cursor_down()

    def action_cursor_up(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_cursor_up()

    def action_first(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_first()

    def action_last(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_last()

    def action_page_down(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_page_down()

    def action_page_up(self) -> None:
        if isinstance(self.focused, OptionList):
            self.focused.action_page_up()

    # --- module <-> pane sync -------------------------------------------------

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        context_pane = self.query_one("#context-pane", ContextPane)
        collection_pane = self.query_one("#collection-pane", CollectionPane)
        if event.option_list is context_pane:
            self._refresh_collection_pane()
            self._refresh_detail_pane()
        elif event.option_list is collection_pane:
            self._refresh_detail_pane()

    def _refresh_context_pane(self) -> None:
        context_pane = self.query_one("#context-pane", ContextPane)
        context_pane.update_contents(self.module.context_pane())

    def _refresh_collection_pane(self) -> None:
        context_item = self.query_one("#context-pane", ContextPane).selected_item
        contents = self.module.collection_pane(context_item)
        self.query_one("#collection-pane", CollectionPane).update_contents(contents)

    def _refresh_detail_pane(self) -> None:
        collection_pane = self.query_one("#collection-pane", CollectionPane)
        contents = self.module.detail_pane(collection_pane.selected_item)
        self.query_one("#detail-pane", DetailPane).update_contents(contents)

    def _refresh_status_bar(self) -> None:
        self.query_one("#status-bar", StatusBar).show_status(mode=Mode.NORMAL)
