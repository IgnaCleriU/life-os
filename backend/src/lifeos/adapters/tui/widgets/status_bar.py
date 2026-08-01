from __future__ import annotations

from textual.widgets import Static

from lifeos.adapters.tui.modes import Mode


class StatusBar(Static):
    """Current mode, active filter, and key hints for the focused pane."""

    def show_status(
        self,
        *,
        mode: Mode,
        filter_text: str = "",
        hints: list[tuple[str, str]] | None = None,
        last_action: str = "",
    ) -> None:
        parts = [mode.value.upper()]
        if filter_text:
            parts.append(f"/{filter_text}")
        if last_action:
            parts.append(last_action)
        if hints:
            parts.append("  ".join(f"{key} {label}" for key, label in hints))
        self.update("  ".join(parts))
