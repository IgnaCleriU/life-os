from __future__ import annotations

from contextlib import contextmanager

from textual.app import App

from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.keymap import KeymapEntry
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.widgets.status_bar import StatusBar


class _EmptyModule:
    def context_pane(self) -> PaneContents:
        return PaneContents(title="CONTEXT", items=[])

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        return PaneContents(title="COLLECTION", items=[])

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        return None

    def keymap_entries(self) -> list[KeymapEntry]:
        return []


# --- confirm() -----------------------------------------------------------


async def test_confirm_calls_on_yes_when_confirmed() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test() as pilot:
        calls: list[str] = []
        app.screen.confirm("sure?", on_yes=lambda: calls.append("yes"))
        await pilot.press("y")
        assert calls == ["yes"]


async def test_confirm_does_not_call_on_yes_when_declined() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test() as pilot:
        calls: list[str] = []
        app.screen.confirm("sure?", on_yes=lambda: calls.append("yes"))
        await pilot.press("n")
        assert calls == []


# --- pick_option() ---------------------------------------------------------


async def test_pick_option_calls_on_select_with_the_chosen_option() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test() as pilot:
        picked: list[str] = []
        options = ["low", "medium", "high"]
        app.screen.pick_option("priority", options, on_select=picked.append)
        await pilot.press("down")
        await pilot.press("enter")
        assert picked == ["medium"]


async def test_pick_option_does_not_call_on_select_when_cancelled() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test() as pilot:
        picked: list[str] = []
        options = ["low", "medium", "high"]
        app.screen.pick_option("priority", options, on_select=picked.append)
        await pilot.press("escape")
        assert picked == []


# --- show_error() / error slot ---------------------------------------------


async def test_show_error_sets_the_status_bar_error_slot() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        app.screen.show_error("project_not_empty: still has live tasks")
        status_bar = app.screen.query_one("#status-bar", StatusBar)
        assert "project_not_empty" in str(status_bar.render())


async def test_action_reload_clears_the_error_slot() -> None:
    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        screen = app.screen
        screen.show_error("something went wrong")
        screen.action_reload()
        status_bar = app.screen.query_one("#status-bar", StatusBar)
        assert "something went wrong" not in str(status_bar.render())


# --- edit_in_external_editor() ---------------------------------------------


async def test_edit_in_external_editor_returns_the_edited_content(monkeypatch) -> None:  # noqa: ANN001
    written: dict[str, str] = {}

    def fake_run(args: list[str], **kwargs: object) -> None:
        path = args[-1]
        with open(path, "w") as f:
            f.write("edited content")
        written["path"] = path

    @contextmanager
    def fake_suspend(self):  # noqa: ANN001, ANN202
        yield

    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(App, "suspend", fake_suspend)

    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        result = app.screen.edit_in_external_editor("original content")
        assert result == "edited content"


async def test_copy_to_clipboard_delegates_to_the_app(monkeypatch) -> None:  # noqa: ANN001
    app = ShellApp(module=_EmptyModule())
    async with app.run_test():
        copied: list[str] = []

        def fake_copy(self, text: str) -> None:  # noqa: ANN001
            copied.append(text)

        monkeypatch.setattr(App, "copy_to_clipboard", fake_copy)
        app.screen.copy_to_clipboard("hello")
        assert copied == ["hello"]
