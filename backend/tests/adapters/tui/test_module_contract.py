"""Tests for the TuiModule Protocol and its value objects (PaneItem,
PaneContents, DetailContents).

Zero Projects/Tasks/use-case code here — the module contract is what lets
the shell stay ignorant of any concrete domain, so these tests only ever
construct hand-written fakes.
"""

from __future__ import annotations

import dataclasses

import pytest

from lifeos.adapters.tui.module import (
    DetailContents,
    PaneContents,
    PaneItem,
    TuiModule,
)


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


class _MissingKeymapEntriesModule:
    """Implements 3 of 4 TuiModule methods — deliberately missing
    keymap_entries(), to prove isinstance() actually discriminates rather
    than being vacuously true for any class."""

    def context_pane(self):
        return None

    def collection_pane(self, context_item):
        return None

    def detail_pane(self, collection_item):
        return None


class TestTuiModuleProtocolRejectsIncompleteImplementations:
    def test_class_missing_one_method_does_not_satisfy_protocol(self) -> None:
        incomplete = _MissingKeymapEntriesModule()

        assert not isinstance(incomplete, TuiModule)


class TestValueObjectsAreFrozen:
    def test_pane_item_is_frozen(self) -> None:
        item = PaneItem(id="1", label="Task 1", payload=None)

        with pytest.raises(dataclasses.FrozenInstanceError):
            item.label = "mutated"

    def test_pane_contents_is_frozen(self) -> None:
        contents = PaneContents(title="Tasks", items=[])

        with pytest.raises(dataclasses.FrozenInstanceError):
            contents.title = "mutated"

    def test_detail_contents_is_frozen(self) -> None:
        detail = DetailContents(title="Task 1", fields=[])

        with pytest.raises(dataclasses.FrozenInstanceError):
            detail.title = "mutated"
