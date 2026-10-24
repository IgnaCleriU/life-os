"""Keymap registry: scopes, entries, and the single source of truth for
which typed key sequence triggers which action in which pane.

Pure Python — no Textual import here. `key` on a `KeymapEntry` is always
the canonical typed sequence ("a", "^k", "gg", "dd"), never a Textual
binding string.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class Scope(str, Enum):
    GLOBAL = "global"
    CONTEXT = "context"
    COLLECTION = "collection"
    DETAIL = "detail"


@dataclass(frozen=True)
class KeymapEntry:
    scope: Scope
    key: str
    label: str
    action: Callable[[], None]
    is_sequence_prefix_of: str | None = None


def undeclared_prefix_collisions(
    entries: list[KeymapEntry],
) -> list[tuple[KeymapEntry, KeymapEntry]]:
    """Pairs (shorter, longer) where shorter.key is a strict prefix of
    longer.key and shorter.is_sequence_prefix_of != longer.key.

    Empty means no undeclared collisions. This is the mechanism that makes
    the class of bug ADR 0008 had before its Step 12 amendment (`d` due
    date colliding with `dd` delete — `d` is simultaneously a complete
    binding and a strict prefix of `dd`) structurally impossible to
    reintroduce silently: any future entry whose key is a strict prefix of
    another entry's key, without explicitly declaring that relationship,
    is flagged.
    """
    collisions: list[tuple[KeymapEntry, KeymapEntry]] = []
    for shorter in entries:
        for longer in entries:
            if shorter is longer:
                continue
            if not longer.key.startswith(shorter.key):
                continue
            if len(shorter.key) >= len(longer.key):
                continue
            if shorter.is_sequence_prefix_of == longer.key:
                continue
            collisions.append((shorter, longer))
    return collisions


class KeymapRegistry:
    def __init__(self, entries: list[KeymapEntry]) -> None:
        self._entries = list(entries)

    def all(self) -> list[KeymapEntry]:
        return list(self._entries)

    def for_scope(self, scope: Scope) -> list[KeymapEntry]:
        """GLOBAL entries plus entries declared for exactly this scope —
        the effective view for whichever pane is focused."""
        return [
            entry
            for entry in self._entries
            if entry.scope is Scope.GLOBAL or entry.scope is scope
        ]

    def resolve(self, scope: Scope, key: str) -> KeymapEntry | None:
        """Exact match within for_scope(scope), else None."""
        for entry in self.for_scope(scope):
            if entry.key == key:
                return entry
        return None

    def is_prefix(self, scope: Scope, key: str) -> bool:
        """True if `key` is a strict prefix of some longer bound key in
        for_scope(scope)."""
        return any(
            entry.key != key and entry.key.startswith(key)
            for entry in self.for_scope(scope)
        )
