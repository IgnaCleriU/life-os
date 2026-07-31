"""Tests for KeySequenceBuffer: the pure, synchronously-testable state
machine that sits in front of the keymap registry to handle multi-key
chords ("gg", "dd") and leading vim-style digit counts.

No Textual/event loop needed — feed() is driven directly with literal
key strings.
"""

from __future__ import annotations

from lifeos.adapters.tui.dispatch import FeedResult, KeySequenceBuffer
from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope


def _noop() -> None:
    """Placeholder action for KeymapEntry construction in tests."""


class TestSingleKeyExactMatch:
    def test_single_key_exact_match_dispatches_immediately(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])
        buffer = KeySequenceBuffer(registry=registry)

        result = buffer.feed(Scope.COLLECTION, "a")

        assert result == FeedResult.matched(entry)
