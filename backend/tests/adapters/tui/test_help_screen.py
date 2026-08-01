from __future__ import annotations

from textual.app import App
from textual.widgets import Static

from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.screens.help_screen import HelpScreen
from lifeos.adapters.tui.screens.shell_screen import ShellScreen


class _EmptyModule:
    def context_pane(self) -> PaneContents:
        return PaneContents(title="CONTEXT", items=[])

    def collection_pane(self, context_item: PaneItem | None) -> PaneContents:
        return PaneContents(title="COLLECTION", items=[])

    def detail_pane(self, collection_item: PaneItem | None) -> DetailContents | None:
        return None

    def keymap_entries(self) -> list[KeymapEntry]:
        return []


class _ShellHarness(App[None]):
    def on_mount(self) -> None:
        self.push_screen(ShellScreen(module=_EmptyModule()))


def _registry_with(*pairs: tuple[Scope, str, str]) -> KeymapRegistry:
    entries = [
        KeymapEntry(scope, key, label, lambda: None) for scope, key, label in pairs
    ]
    return KeymapRegistry(entries)


async def test_help_screen_lists_every_registry_entry() -> None:
    registry = _registry_with(
        (Scope.GLOBAL, "q", "quit"),
        (Scope.COLLECTION, "dd", "delete, with confirmation"),
    )

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(HelpScreen(registry))

    app = Harness()
    async with app.run_test():
        rendered = str(app.screen.query_one("#help-content", Static).render())
        assert "q" in rendered and "quit" in rendered
        assert "dd" in rendered and "delete, with confirmation" in rendered


async def test_help_screen_structurally_cannot_drift_from_the_registry() -> None:
    # Not a hardcoded expectation - build an arbitrary registry and assert
    # every single entry's key and label show up, proving the screen is
    # generated from whatever the registry contains rather than a fixed list.
    registry = _registry_with(
        (Scope.GLOBAL, "^k", "command palette"),
        (Scope.CONTEXT, "a", "create a project"),
        (Scope.DETAIL, "E", "edit in $EDITOR"),
    )

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(HelpScreen(registry))

    app = Harness()
    async with app.run_test():
        rendered = str(app.screen.query_one("#help-content", Static).render())
        for entry in registry.all():
            assert entry.key in rendered
            assert entry.label in rendered


async def test_escape_closes_the_help_screen() -> None:
    registry = _registry_with((Scope.GLOBAL, "q", "quit"))

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(HelpScreen(registry))

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        assert not isinstance(app.screen, HelpScreen)


async def test_question_mark_opens_help_from_the_shell_and_escape_returns() -> None:
    app = _ShellHarness()
    async with app.run_test() as pilot:
        await pilot.press("question_mark")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, ShellScreen)
