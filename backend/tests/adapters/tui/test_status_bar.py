from textual.app import App, ComposeResult

from lifeos.adapters.tui.modes import Mode
from lifeos.adapters.tui.widgets.status_bar import StatusBar


class _StatusBarHarness(App):
    def compose(self) -> ComposeResult:
        yield StatusBar(id="status")


async def test_status_bar_shows_the_mode_name() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.NORMAL)
        assert "NORMAL" in str(bar.render())


async def test_status_bar_reflects_a_different_mode() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.FILTER)
        assert "FILTER" in str(bar.render())


async def test_status_bar_omits_filter_section_when_filter_text_is_empty() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.NORMAL, filter_text="")
        assert "/" not in str(bar.render())


async def test_status_bar_shows_filter_text_when_present() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.FILTER, filter_text="groceries")
        assert "groceries" in str(bar.render())


async def test_status_bar_shows_key_hints_for_the_focused_pane() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(
            mode=Mode.NORMAL,
            hints=[("a", "add"), ("dd", "delete"), ("?", "help")],
        )
        rendered = str(bar.render())
        assert "a add" in rendered or ("a" in rendered and "add" in rendered)
        assert "dd" in rendered and "delete" in rendered
        assert "?" in rendered and "help" in rendered


async def test_status_bar_hints_default_to_empty_when_omitted() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.NORMAL)
        # Must not raise, and must still show the mode.
        assert "NORMAL" in str(bar.render())


async def test_status_bar_shows_the_last_action_description_when_present() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.NORMAL, last_action="undo: delete task")
        assert "undo: delete task" in str(bar.render())


async def test_status_bar_omits_last_action_section_when_absent() -> None:
    app = _StatusBarHarness()
    async with app.run_test():
        bar = app.query_one("#status", StatusBar)
        bar.show_status(mode=Mode.NORMAL)
        # Just the mode name, nothing stray left over from a default value.
        assert str(bar.render()).strip() == "NORMAL"
