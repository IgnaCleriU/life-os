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

    Shell-access convention (not a formal part of this Protocol, since not
    every module needs it): `ShellScreen.__init__` sets `module.shell` to
    itself *before* calling `keymap_entries()`, so a module wanting to
    trigger shell-level behavior from its own actions - pushing an undoable
    write onto `shell.undo_stack`, opening a text prompt via
    `shell.prompt_insert(...)`, or forcing a re-render via
    `shell.action_reload()` - declares `self.shell: ShellScreen | None =
    None` in its own `__init__` and reads it back from within its action
    closures, built fresh each time `keymap_entries()` runs.
    """

    def context_pane(self) -> PaneContents: ...
    def collection_pane(self, context_item: PaneItem | None) -> PaneContents: ...
    def detail_pane(
        self, collection_item: PaneItem | None
    ) -> DetailContents | None: ...
    def keymap_entries(self) -> list[KeymapEntry]: ...
