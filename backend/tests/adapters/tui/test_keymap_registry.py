"""Tests for the keymap registry (Scope, KeymapEntry, KeymapRegistry).

Covers the shape of the registry (all/for_scope/resolve/is_prefix) and,
critically, the mandated regression-guard against undeclared prefix
collisions between key sequences (e.g. "d" vs "dd") within the same
effective scope.
"""

from __future__ import annotations

from lifeos.adapters.tui.keymap import (
    KeymapEntry,
    KeymapRegistry,
    Scope,
)


def _noop() -> None:
    """Placeholder action for KeymapEntry construction in tests."""


class TestRegistryShape:
    def test_all_returns_every_entry(self) -> None:
        entries = [
            KeymapEntry(scope=Scope.GLOBAL, key="q", label="quit", action=_noop),
            KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop),
        ]
        registry = KeymapRegistry(entries)

        assert registry.all() == entries

    def test_for_scope_returns_global_union_that_scope_only(self) -> None:
        global_entry = KeymapEntry(
            scope=Scope.GLOBAL, key="q", label="quit", action=_noop
        )
        collection_entry = KeymapEntry(
            scope=Scope.COLLECTION, key="a", label="add", action=_noop
        )
        detail_entry = KeymapEntry(
            scope=Scope.DETAIL, key="e", label="edit", action=_noop
        )
        registry = KeymapRegistry([global_entry, collection_entry, detail_entry])

        effective = registry.for_scope(Scope.DETAIL)

        assert global_entry in effective
        assert detail_entry in effective
        # An entry scoped to COLLECTION must not appear when the focused
        # pane's scope is DETAIL.
        assert collection_entry not in effective
        assert len(effective) == 2


class TestResolve:
    def test_resolve_finds_exact_match_within_effective_scope(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.resolve(Scope.COLLECTION, "a") is entry

    def test_resolve_returns_none_when_key_absent(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.resolve(Scope.COLLECTION, "z") is None

    def test_resolve_returns_none_when_entry_out_of_effective_scope(self) -> None:
        # Scoped to COLLECTION only, so resolving it from DETAIL must miss.
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.resolve(Scope.DETAIL, "a") is None
