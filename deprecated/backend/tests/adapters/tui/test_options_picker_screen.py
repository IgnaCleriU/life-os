from __future__ import annotations

from textual.app import App
from textual.widgets import Label

from lifeos.adapters.tui.screens.options_picker_screen import OptionsPickerScreen


class _Harness(App[None]):
    def on_mount(self) -> None:
        self.push_screen(OptionsPickerScreen("priority", ["low", "medium", "high"]))


async def test_lists_every_option() -> None:
    app = _Harness()
    async with app.run_test():
        screen = app.screen
        assert isinstance(screen, OptionsPickerScreen)
        assert screen.options.option_count == 3


async def test_title_is_actually_laid_out_on_screen() -> None:
    """Regression test: same bug as ConfirmScreen (see
    test_confirm_screen.py::test_message_is_actually_laid_out_on_screen) -
    a bare Static nested in a `width: auto` parent collapses to Size(0, 0)
    instead of sizing to its text. This one happened to pass even before the
    fix (the sibling OptionList's own layout pass papered over it), but the
    title is fixed to Label too for the same reason, defensively.
    """
    app = _Harness()
    async with app.run_test():
        for widget in app.screen.query(Label):
            assert widget.size.width > 0, f"{widget!r} laid out with zero width"
            assert widget.size.height > 0, f"{widget!r} laid out with zero height"


async def test_enter_selects_the_highlighted_option() -> None:
    result: dict[str, object] = {}

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(
                OptionsPickerScreen("priority", ["low", "medium", "high"]),
                callback=lambda r: result.update(r=r),
            )

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("down")  # highlight "medium"
        await pilot.press("enter")
        assert result["r"] == "medium"


async def test_escape_dismisses_with_none() -> None:
    result: dict[str, object] = {}

    class Harness(App[None]):
        def on_mount(self) -> None:
            self.push_screen(
                OptionsPickerScreen("priority", ["low", "medium", "high"]),
                callback=lambda r: result.update(r=r),
            )

    app = Harness()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        assert result["r"] is None
