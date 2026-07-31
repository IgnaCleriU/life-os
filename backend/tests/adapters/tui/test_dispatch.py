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


class TestTwoStageSequence:
    def test_two_stage_sequence_waits_then_matches(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="gg", label="top", action=_noop)
        registry = KeymapRegistry([entry])
        buffer = KeySequenceBuffer(registry=registry)

        first = buffer.feed(Scope.COLLECTION, "g")
        second = buffer.feed(Scope.COLLECTION, "g")

        assert first == FeedResult.waiting()
        assert second == FeedResult.matched(entry)


class TestNoMatchResetsState:
    def test_unrelated_key_returns_no_match_and_resets(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])
        buffer = KeySequenceBuffer(registry=registry)

        unrelated = buffer.feed(Scope.COLLECTION, "z")

        assert unrelated == FeedResult.no_match()

    def test_state_does_not_get_stuck_after_no_match(self) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="a", label="add", action=_noop)
        registry = KeymapRegistry([entry])
        buffer = KeySequenceBuffer(registry=registry)

        buffer.feed(Scope.COLLECTION, "z")
        # A valid key fed afterward must still resolve correctly — proves
        # the no_match branch actually reset pending state rather than
        # leaving "z" (or "za") stuck in the buffer.
        result = buffer.feed(Scope.COLLECTION, "a")

        assert result == FeedResult.matched(entry)


class _CountingRegistry:
    """Spy wrapping a real KeymapRegistry, counting resolve()/is_prefix()
    calls so tests can prove digits never reach either lookup."""

    def __init__(self, registry: KeymapRegistry) -> None:
        self._registry = registry
        self.resolve_calls: list[tuple[Scope, str]] = []
        self.is_prefix_calls: list[tuple[Scope, str]] = []

    def resolve(self, scope: Scope, key: str) -> KeymapEntry | None:
        self.resolve_calls.append((scope, key))
        return self._registry.resolve(scope, key)

    def is_prefix(self, scope: Scope, key: str) -> bool:
        self.is_prefix_calls.append((scope, key))
        return self._registry.is_prefix(scope, key)


class TestDigitsNeverReachRegistry:
    def test_leading_digit_then_registered_key_resolves_without_digit_lookup(
        self,
    ) -> None:
        entry = KeymapEntry(scope=Scope.COLLECTION, key="j", label="down", action=_noop)
        real_registry = KeymapRegistry([entry])
        spy = _CountingRegistry(real_registry)
        buffer = KeySequenceBuffer(registry=spy)  # type: ignore[arg-type]

        digit_result = buffer.feed(Scope.COLLECTION, "5")
        key_result = buffer.feed(Scope.COLLECTION, "j")

        assert digit_result == FeedResult.waiting()
        assert key_result == FeedResult.matched(entry)
        # The digit itself must never have been looked up, and the second
        # feed must resolve plain "j", never "5j" or "5".
        looked_up_keys = [key for _, key in spy.resolve_calls] + [
            key for _, key in spy.is_prefix_calls
        ]
        assert "5" not in looked_up_keys
        assert "5j" not in looked_up_keys
        assert (Scope.COLLECTION, "j") in spy.resolve_calls


class TestPendingPrefixWithNoContinuation:
    def test_no_match_on_second_feed_not_a_stale_match(self) -> None:
        entry = KeymapEntry(
            scope=Scope.COLLECTION, key="dd", label="delete", action=_noop
        )
        registry = KeymapRegistry([entry])
        buffer = KeySequenceBuffer(registry=registry)

        # "d" alone is a strict prefix of "dd", so it waits...
        first = buffer.feed(Scope.COLLECTION, "d")
        # ...but the next key is unrelated to any continuation of "d".
        second = buffer.feed(Scope.COLLECTION, "z")

        assert first == FeedResult.waiting()
        assert second == FeedResult.no_match()
