from __future__ import annotations

from textual.app import App

from lifeos.adapters.tui.keymap import KeymapEntry
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.screens.shell_screen import ShellScreen
from lifeos.adapters.tui.undo import UndoableWrite
from lifeos.adapters.tui.widgets.panes import CollectionPane, ContextPane, DetailPane
from lifeos.adapters.tui.widgets.status_bar import StatusBar


class _FakeModule:
    """Minimal TuiModule fake for exercising ShellScreen in isolation -
    the real stub module (Phase 7) doesn't exist yet."""

    def __init__(self) -> None:
        self.context_items = [
            PaneItem(id="ctx-1", label="alpha", payload="alpha-payload", meta="2"),
            PaneItem(id="ctx-2", label="beta", payload="beta-payload", meta="1"),
            PaneItem(id="ctx-3", label="gamma", payload="gamma-payload", meta="0"),
        ]
        self.collection_items_by_context = {
            "ctx-1": [
                PaneItem(id="col-1", label="first thing", payload="p1"),
                PaneItem(id="col-2", label="second thing", payload="p2"),
            ],
            "ctx-2": [PaneItem(id="col-3", label="only thing", payload="p3")],
            "ctx-3": [],
        }

    def context_pane(self) -> PaneContents:
        return PaneContents(title="CONTEXT", items=self.context_items)

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        if context_item is None:
            return PaneContents(title="COLLECTION", items=[])
        items = self.collection_items_by_context.get(context_item.id, [])
        return PaneContents(title="COLLECTION", items=items)

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        if collection_item is None:
            return None
        fields = [("id", collection_item.id)]
        return DetailContents(title=collection_item.label, fields=fields)

    def keymap_entries(self) -> list[KeymapEntry]:
        return []


class _ShellHarness(App[None]):
    def __init__(self, module: _FakeModule) -> None:
        super().__init__()
        self._module = module

    def on_mount(self) -> None:
        self.push_screen(ShellScreen(module=self._module))


async def test_mounting_populates_and_focuses_the_context_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test():
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.option_count == 3
        assert app.focused is context_pane


async def test_l_and_tab_move_focus_to_collection_pane() -> None:
    for key in ("l", "tab"):
        app = _ShellHarness(_FakeModule())
        async with app.run_test() as pilot:
            await pilot.press(key)
            assert isinstance(app.focused, CollectionPane), f"key={key!r}"


async def test_h_and_shift_tab_move_focus_back_to_context_pane() -> None:
    for key in ("h", "shift+tab"):
        app = _ShellHarness(_FakeModule())
        async with app.run_test() as pilot:
            await pilot.press("l")  # to collection
            await pilot.press(key)  # back to context
            assert isinstance(app.focused, ContextPane), f"key={key!r}"


async def test_focus_does_not_move_past_the_rightmost_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        # context -> collection -> detail -> (clamped)
        await pilot.press("l", "l", "l", "l")
        assert isinstance(app.focused, DetailPane)


async def test_focus_does_not_move_past_the_leftmost_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        await pilot.press("h", "h")  # already on context, stays there
        assert isinstance(app.focused, ContextPane)


async def test_j_moves_the_cursor_down_in_the_focused_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.highlighted == 0
        await pilot.press("j")
        assert context_pane.highlighted == 1


async def test_k_moves_the_cursor_up_in_the_focused_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        await pilot.press("j", "j")
        assert context_pane.highlighted == 2
        await pilot.press("k")
        assert context_pane.highlighted == 1


async def test_gg_jumps_to_the_first_item() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        await pilot.press("j", "j")
        assert context_pane.highlighted == 2
        await pilot.press("g", "g")
        assert context_pane.highlighted == 0


async def test_capital_g_jumps_to_the_last_item() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        await pilot.press("G")
        assert context_pane.highlighted == 2


async def test_single_g_alone_does_not_dispatch_anything() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        await pilot.press("g")  # waiting for a second 'g' - no crash, no move
        assert context_pane.highlighted == 0


async def test_selecting_a_context_item_repopulates_the_collection_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        await pilot.press("j")  # highlight ctx-2 ("beta")
        collection_pane = app.screen.query_one("#collection-pane", CollectionPane)
        assert collection_pane.option_count == 1
        prompt = str(collection_pane.get_option_at_index(0).prompt)
        assert "only thing" in prompt


async def test_selecting_a_collection_item_populates_the_detail_pane() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        await pilot.press("l")  # focus collection pane (2 items under ctx-1)
        collection_pane = app.screen.query_one("#collection-pane", CollectionPane)
        assert collection_pane.highlighted == 0
        detail_pane = app.screen.query_one("#detail-pane", DetailPane)
        rendered = str(detail_pane.render())
        assert "first thing" in rendered


async def test_changing_context_selection_clears_stale_detail_content() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        await pilot.press("l")  # detail now shows "first thing" (ctx-1's first item)
        await pilot.press("h")  # back to context
        await pilot.press("j")  # move to ctx-2 ("beta"), which has "only thing"
        detail_pane = app.screen.query_one("#detail-pane", DetailPane)
        rendered = str(detail_pane.render())
        assert "first thing" not in rendered


async def test_status_bar_is_present_and_shows_normal_mode() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        del pilot
        status_bar = app.screen.query_one("#status-bar", StatusBar)
        assert "NORMAL" in str(status_bar.render())


# --- undo/redo global key wiring ----------------------------------------------


async def test_u_calls_undo_on_the_most_recent_write() -> None:

    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        calls: list[str] = []
        write = UndoableWrite(
            "toggle flag",
            undo=lambda: calls.append("undo"),
            redo=lambda: calls.append("redo"),
        )
        app.screen.undo_stack.push(write)
        await pilot.press("u")
        assert calls == ["undo"]


async def test_ctrl_r_calls_redo_after_an_undo() -> None:

    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        calls: list[str] = []
        write = UndoableWrite(
            "toggle flag",
            undo=lambda: calls.append("undo"),
            redo=lambda: calls.append("redo"),
        )
        app.screen.undo_stack.push(write)
        await pilot.press("u")
        await pilot.press("ctrl+r")
        assert calls == ["undo", "redo"]


async def test_u_on_an_empty_undo_stack_does_not_raise() -> None:
    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        await pilot.press("u")  # must not raise


async def test_status_bar_shows_the_last_undo_description() -> None:

    app = _ShellHarness(_FakeModule())
    async with app.run_test() as pilot:
        write = UndoableWrite("delete task", undo=lambda: None, redo=lambda: None)
        app.screen.undo_stack.push(write)
        await pilot.press("u")
        status_bar = app.screen.query_one("#status-bar", StatusBar)
        assert "undo: delete task" in str(status_bar.render())


async def test_undo_refreshes_panes_from_current_module_state() -> None:

    module = _FakeModule()
    app = _ShellHarness(module)
    async with app.run_test() as pilot:
        write = UndoableWrite("noop", undo=lambda: None, redo=lambda: None)
        app.screen.undo_stack.push(write)
        # Mutate the module's data between the write and the undo, proving
        # the pane is re-fetched fresh rather than restored from a snapshot
        # taken when the write was pushed.
        module.context_items.append(PaneItem(id="ctx-4", label="delta", payload=None))
        await pilot.press("u")
        context_pane = app.screen.query_one("#context-pane", ContextPane)
        assert context_pane.option_count == 4


async def test_module_gets_the_undo_stack_before_keymap_entries_is_built() -> None:
    # Convention (see TuiModule's docstring): the shell injects its own
    # undo_stack onto the module as a plain attribute *before* calling
    # keymap_entries(), so a module's own action closures can capture a
    # working reference and push writes onto the same stack u/ctrl+r drive.
    class _UndoAwareModule:
        def __init__(self) -> None:
            self.undo_stack = None
            self.seen_at_keymap_entries_time: object = "unset"

        def context_pane(self) -> PaneContents:
            return PaneContents(title="x", items=[])

        def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
            return PaneContents(title="x", items=[])

        def detail_pane(
            self, collection_item: PaneItem | None
        ) -> DetailContents | None:
            return None

        def keymap_entries(self) -> list[KeymapEntry]:
            self.seen_at_keymap_entries_time = self.undo_stack
            return []

    module = _UndoAwareModule()
    app = _ShellHarness(module)
    async with app.run_test():
        assert module.seen_at_keymap_entries_time is app.screen.undo_stack
        assert module.seen_at_keymap_entries_time is not None
