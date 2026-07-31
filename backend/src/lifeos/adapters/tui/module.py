"""TuiModule contract: the boundary between the generic shell and a
concrete domain module (e.g. the future Projects/Tasks module).

The shell never imports `application`/`domain`/`infrastructure` — it only
knows PaneItem (a stable id + label + opaque payload), PaneContents,
DetailContents, and the TuiModule Protocol. A real module wraps actual
domain entities in `payload`; the shell never inspects it and hands back
exactly the PaneItem it was given on selection change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from lifeos.adapters.tui.keymap import KeymapEntry


@dataclass(frozen=True)
class PaneItem:
    id: str
    label: str
    payload: Any
    meta: str = ""


@dataclass(frozen=True)
class PaneContents:
    title: str
    items: list[PaneItem]


@dataclass(frozen=True)
class DetailContents:
    title: str
    fields: list[tuple[str, str]]


@runtime_checkable
class TuiModule(Protocol):
    """A module supplies pane content and its own key bindings; the shell
    calls it, never the other way around.

    Undo convention (not a formal part of this Protocol, since not every
    module performs writes): `ShellScreen.__init__` sets `module.undo_stack`
    to its own `UndoStack` instance *before* calling `keymap_entries()`, so
    a module wanting undo support declares `self.undo_stack: UndoStack |
    None = None` in its own `__init__` and reads it back from within its own
    action closures - the same stack `u`/`ctrl+r` drive, not a private copy.
    """

    def context_pane(self) -> PaneContents: ...
    def collection_pane(self, context_item: PaneItem | None) -> PaneContents: ...
    def detail_pane(
        self, collection_item: PaneItem | None
    ) -> DetailContents | None: ...
    def keymap_entries(self) -> list[KeymapEntry]: ...
