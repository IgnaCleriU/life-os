"""Tests for the TuiModule Protocol and its value objects (PaneItem,
PaneContents, DetailContents).

Zero Projects/Tasks/use-case code here — the module contract is what lets
the shell stay ignorant of any concrete domain, so these tests only ever
construct hand-written fakes.
"""

from __future__ import annotations

from lifeos.adapters.tui.module import TuiModule


class _CompleteFakeModule:
    """Implements all four TuiModule methods."""

    def context_pane(self):
        return None

    def collection_pane(self, context_item):
        return None

    def detail_pane(self, collection_item):
        return None

    def keymap_entries(self):
        return []


class TestTuiModuleProtocolConformance:
    def test_class_implementing_all_four_methods_satisfies_protocol(self) -> None:
        fake = _CompleteFakeModule()

        assert isinstance(fake, TuiModule)
