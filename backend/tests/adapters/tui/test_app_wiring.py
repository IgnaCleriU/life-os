from __future__ import annotations

from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.keymap import KeymapEntry
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.modules.stub import StubModule
from lifeos.adapters.tui.screens.help_screen import HelpScreen
from lifeos.adapters.tui.screens.palette_screen import PaletteScreen
from lifeos.adapters.tui.screens.shell_screen import ShellScreen
from lifeos.adapters.tui.widgets.panes import ContextPane, DetailPane


class _EmptyModule:
    """Bare-minimum TuiModule fake - just enough for ShellApp to boot."""

    def context_pane(self) -> PaneContents:
        return PaneContents(title="CONTEXT", items=[])

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        return PaneContents(title="COLLECTION", items=[])

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        return None

    def keymap_entries(self) -> list[KeymapEntry]:
        return []


async def test_shell_app_boots_and_pushes_the_shell_screen() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        assert isinstance(app.screen, ShellScreen)
        assert isinstance(app.screen.query_one("#context-pane"), ContextPane)


async def test_shell_app_disables_the_builtin_command_palette() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        assert app.ENABLE_COMMAND_PALETTE is False


async def test_q_quits_the_app() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test() as pilot:
        await pilot.press("q")
        assert not app.is_running


async def test_capital_r_reloads_all_panes_from_the_module() -> None:
    module = _EmptyModule()
    app = ShellApp(module=module)
    async with app.run_test() as pilot:
        module.context_pane = lambda: PaneContents(  # type: ignore[method-assign]
            title="CONTEXT", items=[PaneItem(id="x", label="new item", payload=None)]
        )
        await pilot.press("R")
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.option_count == 1


# --- end-to-end integration against the real stub module ----------------------


async def test_end_to_end_nav_palette_help_insert_undo_quit() -> None:
    app = ShellApp(module=StubModule())
    async with app.run_test() as pilot:
        # navigation
        await pilot.press("j")
        await pilot.press("l")
        assert isinstance(app.screen, ShellScreen)

        # palette opens, executing an entry closes it
        await pilot.press("ctrl+k")
        assert isinstance(app.screen, PaletteScreen)
        await pilot.press("enter")
        assert isinstance(app.screen, ShellScreen)

        # help opens and Esc closes it
        await pilot.press("question_mark")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, ShellScreen)

        # insert: add a bucket via the context pane's "a" action
        await pilot.press("h")
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        before = context_pane.option_count
        await pilot.press("a")
        await pilot.press("z", "z", "z")
        await pilot.press("enter")
        assert context_pane.option_count == before + 1

        # toggle + undo on a collection item
        await pilot.press("h", "l")
        detail_pane = app.screen.query_one("#detail-pane", DetailPane)
        before_flag = str(detail_pane.render())
        await pilot.press("t")
        assert str(detail_pane.render()) != before_flag
        await pilot.press("u")
        assert str(detail_pane.render()) == before_flag

        # quit
        await pilot.press("q")
        assert not app.is_running
