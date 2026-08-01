from __future__ import annotations

from textual.app import App
from textual.widgets import Static

from lifeos.adapters.tui.screens.confirm_screen import ConfirmScreen


class _Harness(App[None]):
    def on_mount(self) -> None:
        self.push_screen(ConfirmScreen("delete this task?"))


async def test_shows_the_message() -> None:
    app = _Harness()
    async with app.run_test():
        rendered = "\n".join(str(w.render()) for w in app.screen.query(Static))
        assert "delete this task?" in rendered


async def test_y_confirms_true() -> None:
    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.press("y")
        assert not isinstance(app.screen, ConfirmScreen)


async def test_enter_confirms_true() -> None:
    result: dict[str, object] = {}

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(
                ConfirmScreen("sure?"), callback=lambda r: result.update(r=r)
            )

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert result["r"] is True


async def test_n_cancels_false() -> None:
    result: dict[str, object] = {}

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(
                ConfirmScreen("sure?"), callback=lambda r: result.update(r=r)
            )

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("n")
        assert result["r"] is False


async def test_escape_cancels_false() -> None:
    result: dict[str, object] = {}

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(
                ConfirmScreen("sure?"), callback=lambda r: result.update(r=r)
            )

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        assert result["r"] is False
