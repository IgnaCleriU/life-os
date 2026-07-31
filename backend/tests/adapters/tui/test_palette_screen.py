from __future__ import annotations

from textual.app import App
from textual.widgets import Input

from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope
from lifeos.adapters.tui.modes import Mode
from lifeos.adapters.tui.module import DetailContents, PaneContents, PaneItem
from lifeos.adapters.tui.screens.palette_screen import PaletteScreen
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


def _registry_with(*labels: str) -> tuple[KeymapRegistry, list[str]]:
    calls: list[str] = []

    def _record(label: str) -> None:
        calls.append(label)

    entries = [
        KeymapEntry(Scope.GLOBAL, str(i), label, lambda label=label: _record(label))
        for i, label in enumerate(labels)
    ]
    return KeymapRegistry(entries), calls


# --- standalone PaletteScreen behavior ---------------------------------------


async def test_palette_lists_every_registry_entry_on_open() -> None:
    registry, _ = _registry_with("add project", "delete task", "quit")

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(PaletteScreen(registry))

    app = Harness()
    async with app.run_test():
        screen = app.screen
        assert isinstance(screen, PaletteScreen)
        rendered = "\n".join(
            str(screen.results.get_option_at_index(i).prompt)
            for i in range(screen.results.option_count)
        )
        assert "add project" in rendered
        assert "delete task" in rendered
        assert "quit" in rendered


async def test_typing_filters_the_palette_results() -> None:
    registry, _ = _registry_with("add project", "delete task", "quit")

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(PaletteScreen(registry))

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("d", "e", "l")
        screen = app.screen
        assert screen.results.option_count == 1
        assert "delete task" in str(screen.results.get_option_at_index(0).prompt)


async def test_selecting_an_entry_invokes_its_action_and_closes() -> None:
    registry, calls = _registry_with("add project", "delete task")

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(PaletteScreen(registry))

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("enter")  # first result highlighted by default
        assert calls == ["add project"]
        assert not isinstance(app.screen, PaletteScreen)


async def test_escape_closes_the_palette_without_invoking_anything() -> None:
    registry, calls = _registry_with("add project")

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(PaletteScreen(registry))

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        assert calls == []
        assert not isinstance(app.screen, PaletteScreen)


# --- wired through ShellScreen's ^k binding -----------------------------------


async def test_ctrl_k_opens_the_palette_from_the_shell() -> None:
    app = _ShellHarness()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+k")
        assert isinstance(app.screen, PaletteScreen)
        assert isinstance(app.screen.query_one(Input), Input)


async def test_closing_the_palette_returns_shell_to_normal_mode() -> None:
    app = _ShellHarness()
    async with app.run_test() as pilot:
        shell_screen = app.screen
        assert isinstance(shell_screen, ShellScreen)
        await pilot.press("ctrl+k")
        assert shell_screen.mode_controller.mode == Mode.PALETTE
        await pilot.press("escape")
        assert isinstance(app.screen, ShellScreen)
        assert shell_screen.mode_controller.mode == Mode.NORMAL
