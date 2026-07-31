from __future__ import annotations

from textual.app import App

from lifeos.adapters.tui.module import TuiModule
from lifeos.adapters.tui.screens.shell_screen import ShellScreen


class ShellApp(App[None]):
    """Top-level Textual App. Textual's own command palette is disabled -
    ADR 0008 wants a single command list (the keymap registry), and
    Textual's built-in palette is a second, separate one.
    """

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, module: TuiModule) -> None:
        super().__init__()
        self.module = module

    def on_mount(self) -> None:
        self.push_screen(ShellScreen(module=self.module))
