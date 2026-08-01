from __future__ import annotations

from textual.app import App
from textual.widgets import Input

from lifeos.adapters.tui.keymap import KeymapEntry, Scope
from lifeos.adapters.tui.modes import Mode
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.screens.shell_screen import ShellScreen
from lifeos.adapters.tui.widgets.panes import ContextPane
from lifeos.adapters.tui.widgets.status_bar import StatusBar


class _FilterableModule:
    def __init__(self) -> None:
        self.items = [
            PaneItem(id="1", label="write adr 0008", payload=None),
            PaneItem(id="2", label="port backend to tui", payload=None),
            PaneItem(id="3", label="write tests", payload=None),
        ]
        self.committed: list[str] = []

    def context_pane(self) -> PaneContents:
        return PaneContents(title="CONTEXT", items=self.items)

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        return PaneContents(title="COLLECTION", items=[])

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        return None

    def keymap_entries(self) -> list[KeymapEntry]:
        return [
            KeymapEntry(
                Mode.NORMAL,  # placeholder scope value unused by this fake
                "a",
                "add via insert prompt",
                self._start_insert,
            )
        ]

    def _start_insert(self) -> None:
        pass  # replaced per-test via monkeypatching the bound screen


class _ShellHarness(App[None]):
    def __init__(self, module: _FilterableModule) -> None:
        super().__init__()
        self.module = module

    def on_mount(self) -> None:
        self.push_screen(ShellScreen(module=self.module))


# --- FILTER mode -------------------------------------------------------------


async def test_slash_enters_filter_mode_and_shows_the_prompt() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        await pilot.press("slash")
        screen = app.screen
        assert screen.mode_controller.mode == Mode.FILTER
        prompt = screen.query_one("#prompt-input", Input)
        assert prompt.display is True
        assert app.focused is prompt


async def test_typing_in_filter_narrows_the_focused_pane_live() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        await pilot.press("slash")
        await pilot.press("w", "r", "i", "t", "e")
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        prompts = [
            str(context_pane.get_option_at_index(i).prompt)
            for i in range(context_pane.option_count)
        ]
        assert all("write" in p for p in prompts)
        assert context_pane.option_count == 2


async def test_escape_cancels_the_filter_and_restores_all_items() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        await pilot.press("slash")
        await pilot.press("w", "r", "i", "t", "e")
        await pilot.press("escape")
        screen = app.screen
        assert screen.mode_controller.mode == Mode.NORMAL
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.option_count == 3
        prompt = screen.query_one("#prompt-input", Input)
        assert prompt.display is False


async def test_enter_commits_the_filter_and_keeps_it_applied() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        await pilot.press("slash")
        await pilot.press("w", "r", "i", "t", "e")
        await pilot.press("enter")
        screen = app.screen
        assert screen.mode_controller.mode == Mode.NORMAL
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.option_count == 2


async def test_status_bar_shows_filter_mode_and_text_while_filtering() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        await pilot.press("slash")
        await pilot.press("w")
        status_bar = app.screen.query_one("#status-bar", StatusBar)
        rendered = str(status_bar.render())
        assert "FILTER" in rendered
        assert "w" in rendered


# --- INSERT mode (generic prompt) --------------------------------------------


async def test_prompt_insert_enters_insert_mode_and_shows_the_prompt() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test():
        screen = app.screen
        screen.prompt_insert(placeholder="add>", on_commit=lambda text: None)
        assert screen.mode_controller.mode == Mode.INSERT
        prompt = screen.query_one("#prompt-input", Input)
        assert prompt.display is True
        assert prompt.placeholder == "add>"


async def test_prompt_insert_enter_commits_typed_text_and_returns_to_normal() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        screen = app.screen
        committed: list[str] = []
        screen.prompt_insert(placeholder="", on_commit=committed.append)
        await pilot.press("h", "i")
        await pilot.press("enter")
        assert committed == ["hi"]
        assert screen.mode_controller.mode == Mode.NORMAL
        prompt = screen.query_one("#prompt-input", Input)
        assert prompt.display is False


async def test_prompt_insert_escape_cancels_without_committing() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        screen = app.screen
        committed: list[str] = []
        screen.prompt_insert(placeholder="", on_commit=committed.append)
        await pilot.press("h", "i")
        await pilot.press("escape")
        assert committed == []
        assert screen.mode_controller.mode == Mode.NORMAL


# --- SELECT mode (generic selection set) --------------------------------------


async def test_enter_select_mode_and_toggle_marks_the_current_item() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test():
        screen = app.screen
        screen.enter_select_mode()
        assert screen.mode_controller.mode == Mode.SELECT
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        current = context_pane.selected_item
        assert current is not None
        screen.toggle_selection(current.id)
        assert current.id in screen.selected_ids


async def test_escape_from_select_mode_clears_the_selection_set() -> None:
    app = _ShellHarness(_FilterableModule())
    async with app.run_test() as pilot:
        screen = app.screen
        screen.enter_select_mode()
        screen.toggle_selection("1")
        await pilot.press("escape")
        assert screen.mode_controller.mode == Mode.NORMAL
        assert screen.selected_ids == set()


def test_entering_select_mode_twice_in_a_row_does_not_raise() -> None:
    """Toggling selection on a second item calls enter_select_mode() while
    already in SELECT mode - this must be a no-op, not a ModeController
    ValueError (ADR: SELECT is a single mode, not a mode you re-enter)."""
    app = _ShellHarness(_FilterableModule())
    screen = ShellScreen(module=app.module)
    screen.enter_select_mode()
    screen.enter_select_mode()
    assert screen.mode_controller.mode == Mode.SELECT


class _TogglingModule(_FilterableModule):
    """Bulk-select toggling as a real keymap action, mirroring
    ProjectsTasksModule._toggle_select: every scoped toggle keypress calls
    enter_select_mode() unconditionally."""

    def keymap_entries(self) -> list[KeymapEntry]:
        return [
            KeymapEntry(Scope.CONTEXT, "x", "toggle selection", self._toggle),
        ]

    def _toggle(self) -> None:
        self.shell.enter_select_mode()
        item = self.shell.current_context_item
        if item is not None:
            self.shell.toggle_selection(item.id)


async def test_pressing_toggle_selection_twice_selects_two_items_without_crashing() -> (
    None
):
    app = _ShellHarness(_TogglingModule())
    async with app.run_test() as pilot:
        screen = app.screen
        await pilot.press("j")  # move off item "1" onto item "2"
        await pilot.press("x")
        await pilot.press("k")  # back onto item "1"
        await pilot.press("x")
        assert screen.selected_ids == {"1", "2"}
