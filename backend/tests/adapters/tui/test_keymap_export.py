"""Exporta el registro de atajos de la TUI al fixture que usa el tablero de
Quickshell (spec 0002).

El tablero reimplementa el keymap en JavaScript
(`desktop/omarchy-plugin/lib/keymap.js`); su test de paridad
(`desktop/tests/keymap.test.mjs`) compara contra este fixture. Este test
falla si el fixture quedó viejo respecto del registro real, así un cambio de
atajos en la TUI no puede divergir en silencio del tablero.

Para regenerarlo: `LIFEOS_UPDATE_KEYMAP_FIXTURE=1 uv run pytest
tests/adapters/tui/test_keymap_export.py`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.adapters.tui.screens.shell_screen import ShellScreen

FIXTURE = Path(__file__).resolve().parents[4] / "desktop" / "tests" / "tui-keymap.json"


def _export() -> list[dict[str, str]]:
    screen = ShellScreen(module=ProjectsTasksModule())
    entries = [
        {"scope": entry.scope.value, "key": entry.key, "label": entry.label}
        for entry in screen.registry.all()
    ]
    return sorted(entries, key=lambda e: (e["scope"], e["key"], e["label"]))


def test_fixture_matches_the_tui_registry() -> None:
    exported = _export()
    if os.environ.get("LIFEOS_UPDATE_KEYMAP_FIXTURE"):
        FIXTURE.write_text(json.dumps(exported, indent=2, ensure_ascii=False) + "\n")

    assert json.loads(FIXTURE.read_text()) == exported, (
        "desktop/tests/tui-keymap.json is stale: regenerate it with "
        "LIFEOS_UPDATE_KEYMAP_FIXTURE=1 and update lib/keymap.js to match"
    )
