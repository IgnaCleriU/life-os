"""TUI shell modality: the 5 ADR 0008 modes and the Esc rule.

Pure Python, no `textual` dependency — see the "Modality" section of
`docs/adr/0008-keyboard-driven-tui-adapter.md`. This module only knows "which
mode is active" and "whether Esc went back one level or not"; everything else
(pane focus, quit confirmation, what *closing* a mode implies — e.g. clearing
a filter's text) is the responsibility of whoever owns that state (the
shell), not this controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(str, Enum):
    """The shell's 5 modes. Exactly one is always active."""

    NORMAL = "normal"
    INSERT = "insert"
    FILTER = "filter"
    SELECT = "select"
    PALETTE = "palette"


@dataclass
class ModeController:
    """Controls transitions between modes and the ADR's Esc rule.

    The ADR models the mode stack with a maximum depth of 2: NORMAL (the
    base level) and, at most, one mode above it. That's the only reading
    consistent with "Esc always goes back exactly one level": if chaining
    from one non-NORMAL mode to another (e.g. FILTER -> PALETTE) were
    allowed, an Esc from the deeper mode would be ambiguous (back to the
    previous mode, or straight to NORMAL?), and the ADR never resolves that
    ambiguity because it doesn't anticipate the case.
    """

    mode: Mode = Mode.NORMAL

    def enter(self, mode: Mode) -> None:
        """Transitions to `mode`, only allowed from NORMAL.

        Chaining between two non-NORMAL modes without passing through
        NORMAL (via `escape()`) is deliberately forbidden — see the class
        docstring. Calling `enter()` while already in a non-NORMAL mode
        raises `ValueError` instead of silently overwriting the mode, so
        any attempt to chain fails loudly at the exact point that caused it.

        `enter(Mode.NORMAL)` is always valid: it isn't an "enterable" mode
        in the ADR's sense (no key "enters NORMAL" — that's reached via
        `escape()`), but treating it as a special case would add a branch
        with no real benefit, since it's already the default value.
        """
        if self.mode is not Mode.NORMAL and mode is not Mode.NORMAL:
            raise ValueError(
                f"cannot enter {mode} directly from {self.mode}; "
                "escape() back to NORMAL first"
            )
        self.mode = mode

    def escape(self) -> bool:
        """Applies the "Esc goes back exactly one level" rule.

        Returns True if this call changed the mode (we were in a
        non-NORMAL mode and are now in NORMAL), False if we were already in
        NORMAL — in which case the caller (the shell, later) must handle
        Esc's NORMAL-mode behavior (pane focus / quit prompt), which this
        controller does not implement.
        """
        if self.mode is Mode.NORMAL:
            return False
        self.mode = Mode.NORMAL
        return True
