from __future__ import annotations

from collections.abc import Callable

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Input, OptionList

from lifeos.adapters.tui.dispatch import KeySequenceBuffer
from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope
from lifeos.adapters.tui.modes import Mode, ModeController
from lifeos.adapters.tui.module import PaneItem, TuiModule
from lifeos.adapters.tui.screens.confirm_screen import ConfirmScreen
from lifeos.adapters.tui.screens.help_screen import HelpScreen
from lifeos.adapters.tui.screens.options_picker_screen import OptionsPickerScreen
from lifeos.adapters.tui.screens.palette_screen import PaletteScreen
from lifeos.adapters.tui.undo import UndoStack
from lifeos.adapters.tui.widgets.panes import (
    CollectionPane,
    ContextPane,
    DetailPane,
    ItemListPane,
)
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
        self.mode_controller = ModeController()
        self.undo_stack = UndoStack()
        self._last_action_description = ""
        self._error_message = ""
        self.selected_ids: set[str] = set()
        # Convention documented on TuiModule: the module reads this back off
        # itself from within its own keymap_entries() action closures, to
        # reach undo_stack / prompt_insert / action_reload etc. - set before
        # keymap_entries() runs, not after.
        module.shell = self  # type: ignore[attr-defined]
        entries = [*self._global_entries(), *module.keymap_entries()]
        self.registry = KeymapRegistry(entries)
        self.buffer = KeySequenceBuffer(self.registry)
        self._filter_pane: ItemListPane | None = None
        self._insert_on_commit: Callable[[str], None] | None = None
        self._pane_before_prompt: Widget | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ContextPane(id="context-pane")
            yield CollectionPane(id="collection-pane")
            yield DetailPane(id="detail-pane")
        yield Input(id="prompt-input")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._refresh_context_pane()
        self.query_one("#context-pane", ContextPane).focus()
        self.query_one("#prompt-input", Input).display = False
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
            KeymapEntry(
                Scope.GLOBAL, "R", "reload from the database", self.action_reload
            ),
            KeymapEntry(Scope.GLOBAL, "q", "quit", self.action_quit),
            KeymapEntry(Scope.GLOBAL, "escape", "back one level", self.action_escape),
            KeymapEntry(Scope.GLOBAL, "slash", "filter", self.action_enter_filter),
            KeymapEntry(
                Scope.GLOBAL, "ctrl+k", "command palette", self.action_open_palette
            ),
            KeymapEntry(
                Scope.GLOBAL,
                "question_mark",
                "keybindings overlay",
                self.action_open_help,
            ),
            KeymapEntry(Scope.GLOBAL, "u", "undo", self.action_undo),
            KeymapEntry(Scope.GLOBAL, "ctrl+r", "redo", self.action_redo),
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

    @property
    def current_context_item(self) -> PaneItem | None:
        return self.query_one("#context-pane", ContextPane).selected_item

    @property
    def current_collection_item(self) -> PaneItem | None:
        return self.query_one("#collection-pane", CollectionPane).selected_item

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

    def action_reload(self) -> None:
        self._error_message = ""
        self._refresh_context_pane()
        self._refresh_collection_pane()
        self._refresh_detail_pane()
        self._refresh_status_bar()

    def action_undo(self) -> None:
        write = self.undo_stack.undo()
        if write is None:
            return
        self._last_action_description = f"undo: {write.description}"
        self.action_reload()

    def action_redo(self) -> None:
        write = self.undo_stack.redo()
        if write is None:
            return
        self._last_action_description = f"redo: {write.description}"
        self.action_reload()

    def action_quit(self) -> None:
        self.app.exit()

    def action_escape(self) -> None:
        previous_mode = self.mode_controller.mode
        if self.mode_controller.escape():
            self._close_mode(previous_mode)
            self._refresh_status_bar()
            return
        # Already NORMAL. ADR 0008: from the leftmost pane, Esc prompts to
        # quit; a real confirmation dialog is more machinery than this
        # domain-agnostic shell needs to invent for Step 12, so it quits
        # directly here, same as `q` - a real module can layer a confirm
        # on top later if that's ever missed in practice.
        if self._pane_index() == 0:
            self.action_quit()
        else:
            self.action_focus_previous_pane()

    def _close_mode(self, mode: Mode) -> None:
        if mode is Mode.FILTER:
            if self._filter_pane is not None:
                self._filter_pane.clear_filter()
            self._hide_prompt()
            self._filter_pane = None
        elif mode is Mode.INSERT:
            self._hide_prompt()
            self._insert_on_commit = None
        elif mode is Mode.SELECT:
            self.selected_ids.clear()

    # --- FILTER mode ---------------------------------------------------------

    def action_enter_filter(self) -> None:
        pane = self.focused
        if not isinstance(pane, ItemListPane):
            return
        self.mode_controller.enter(Mode.FILTER)
        self._filter_pane = pane
        self._show_prompt(placeholder="filter")

    # --- INSERT mode (generic - modules trigger this from their own actions) -

    def prompt_insert(
        self, *, placeholder: str = "", on_commit: Callable[[str], None]
    ) -> None:
        self.mode_controller.enter(Mode.INSERT)
        self._insert_on_commit = on_commit
        self._show_prompt(placeholder=placeholder)

    # --- PALETTE and HELP: independent modal Screens, not shell state --------

    def action_open_palette(self) -> None:
        self.mode_controller.enter(Mode.PALETTE)
        self.app.push_screen(
            PaletteScreen(self.registry), callback=self._on_overlay_closed
        )

    def action_open_help(self) -> None:
        # No dedicated HELP mode exists in ADR 0008's 5-mode table - the
        # overlay covers the whole screen either way, so there's nothing for
        # the status bar underneath to usefully say while it's open.
        self.app.push_screen(HelpScreen(self.registry))

    def _on_overlay_closed(self, _result: None) -> None:
        self.mode_controller.escape()
        self._refresh_status_bar()

    # --- CONFIRM and PICK_OPTION: independent modal Screens, generic --------

    def confirm(self, message: str, *, on_yes: Callable[[], None]) -> None:
        def _callback(confirmed: bool | None) -> None:
            if confirmed:
                on_yes()

        self.app.push_screen(ConfirmScreen(message), callback=_callback)

    def pick_option(
        self, title: str, options: list[str], *, on_select: Callable[[str], None]
    ) -> None:
        def _callback(chosen: str | None) -> None:
            if chosen is not None:
                on_select(chosen)

        self.app.push_screen(OptionsPickerScreen(title, options), callback=_callback)

    def edit_in_external_editor(self, initial_text: str) -> str:
        """Suspends the app, opens `$EDITOR` (falls back to `vi`) on a temp
        file seeded with `initial_text`, and returns its contents after the
        editor exits. Synchronous and blocking, like every other `$EDITOR`
        integration - the app is suspended for the duration anyway."""
        import os
        import subprocess
        import tempfile

        editor = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as handle:
            handle.write(initial_text)
            path = handle.name
        try:
            with self.app.suspend():
                subprocess.run([editor, path], check=False)
            with open(path) as handle:
                return handle.read()
        finally:
            os.unlink(path)

    def show_error(self, message: str) -> None:
        self._error_message = message
        self._refresh_status_bar()

    def copy_to_clipboard(self, text: str) -> None:
        """Thin wrapper over `App.copy_to_clipboard` (OSC 52, no new
        dependency) - kept here so modules only ever talk to `shell.*`,
        never reach past it into `shell.app`."""
        self.app.copy_to_clipboard(text)

    # --- SELECT mode (generic selection set) ----------------------------------

    def enter_select_mode(self) -> None:
        if self.mode_controller.mode is not Mode.SELECT:
            self.mode_controller.enter(Mode.SELECT)
        self._refresh_status_bar()

    def toggle_selection(self, item_id: str) -> None:
        if item_id in self.selected_ids:
            self.selected_ids.discard(item_id)
        else:
            self.selected_ids.add(item_id)

    # --- shared prompt (Input) plumbing for FILTER and INSERT -----------------

    def _show_prompt(self, *, placeholder: str) -> None:
        self._pane_before_prompt = self.focused
        prompt = self.query_one("#prompt-input", Input)
        prompt.placeholder = placeholder
        prompt.value = ""
        prompt.display = True
        prompt.focus()
        self._refresh_status_bar()

    def _hide_prompt(self) -> None:
        prompt = self.query_one("#prompt-input", Input)
        prompt.display = False
        prompt.value = ""
        if self._pane_before_prompt is not None:
            self._pane_before_prompt.focus()
        self._pane_before_prompt = None

    def on_input_changed(self, event: Input.Changed) -> None:
        if self.mode_controller.mode is Mode.FILTER and self._filter_pane is not None:
            self._filter_pane.filter(event.value)
        self._refresh_status_bar()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.mode_controller.mode is Mode.FILTER:
            self.mode_controller.escape()
            self._hide_prompt()
            self._filter_pane = None
            self._refresh_status_bar()
        elif self.mode_controller.mode is Mode.INSERT:
            on_commit = self._insert_on_commit
            self.mode_controller.escape()
            self._hide_prompt()
            self._insert_on_commit = None
            self._refresh_status_bar()
            if on_commit is not None:
                on_commit(event.value)

    # --- module <-> pane sync -------------------------------------------------

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        context_pane = self.query_one("#context-pane", ContextPane)
        collection_pane = self.query_one("#collection-pane", CollectionPane)
        if event.option_list is context_pane:
            # A bulk selection is scoped to the project it was made in - if
            # it survived a context-pane move, a bulk action would silently
            # act on the previous project's stale selection instead of the
            # one now on screen.
            if self.mode_controller.mode is Mode.SELECT:
                self.mode_controller.escape()
                self._refresh_status_bar()
            self.selected_ids.clear()
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
        filter_text = ""
        if self.mode_controller.mode is Mode.FILTER:
            filter_text = self.query_one("#prompt-input", Input).value
        self.query_one("#status-bar", StatusBar).show_status(
            mode=self.mode_controller.mode,
            filter_text=filter_text,
            last_action=self._last_action_description,
            error=self._error_message,
        )
