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
    undeclared_prefix_collisions,
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


class TestIsPrefix:
    def test_is_prefix_true_for_strict_prefix_of_longer_bound_key(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="gg", label="top", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.is_prefix(Scope.COLLECTION, "g") is True

    def test_is_prefix_false_when_key_is_itself_a_complete_binding(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.is_prefix(Scope.COLLECTION, "a") is False

    def test_is_prefix_false_for_key_unrelated_to_any_binding(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="gg", label="top", action=_noop)
        registry = KeymapRegistry([entry])

        assert registry.is_prefix(Scope.COLLECTION, "z") is False


class TestUndeclaredPrefixCollisionsRegressionGuard:
    """The mandated regression-guard test (roadmap requirement, verbatim):

    "adds a keymap-registry test that makes this class of collision
    structurally impossible to reintroduce silently" — i.e. any future
    entry whose key is a strict prefix of another entry's key in the same
    effective scope, without explicitly declaring that relationship via
    `is_sequence_prefix_of`, must fail this test. This is exactly the bug
    ADR 0008 had before its Step 12 amendment: `d` (due date) collided
    with `dd` (delete) because `d` is simultaneously a complete binding
    and a strict prefix of `dd`.
    """

    def test_hand_built_registry_has_no_undeclared_prefix_collisions(self) -> None:
        # A small but non-trivial registry: one GLOBAL, one COLLECTION, one
        # CONTEXT entry, plus a legitimate 2-char sequence ("gg") that has
        # no colliding single-key sibling ("g" is not itself bound to
        # anything, so it's a "waiting" prefix, not an undeclared collision).
        entries = [
            KeymapEntry(scope=Scope.GLOBAL, key="q", label="quit", action=_noop),
            KeymapEntry(
                scope=Scope.GLOBAL, key="^k", label="palette", action=_noop
            ),
            KeymapEntry(
                scope=Scope.CONTEXT, key="j", label="down", action=_noop
            ),
            KeymapEntry(
                scope=Scope.COLLECTION, key="a", label="add", action=_noop
            ),
            KeymapEntry(
                scope=Scope.COLLECTION,
                key="dd",
                label="delete",
                action=_noop,
            ),
            KeymapEntry(
                scope=Scope.COLLECTION, key="gg", label="top", action=_noop
            ),
        ]
        registry = KeymapRegistry(entries)

        assert undeclared_prefix_collisions(registry.all()) == []


class TestUndeclaredPrefixCollisionsHasTeeth:
    """Proves the check actually flags a violation rather than vacuously
    passing — does NOT rely on production data happening to contain one.
    """

    def test_flags_deliberate_undeclared_collision(self) -> None:
        short = KeymapEntry(
            scope=Scope.COLLECTION, key="d", label="due date", action=_noop
        )
        long_ = KeymapEntry(
            scope=Scope.COLLECTION, key="dd", label="delete", action=_noop
        )

        collisions = undeclared_prefix_collisions([short, long_])

        assert collisions == [(short, long_)]

    def test_declaring_the_prefix_relationship_clears_the_collision(self) -> None:
        short = KeymapEntry(
            scope=Scope.COLLECTION,
            key="d",
            label="due date",
            action=_noop,
            is_sequence_prefix_of="dd",
        )
        long_ = KeymapEntry(
            scope=Scope.COLLECTION, key="dd", label="delete", action=_noop
        )

        collisions = undeclared_prefix_collisions([short, long_])

        assert collisions == []
