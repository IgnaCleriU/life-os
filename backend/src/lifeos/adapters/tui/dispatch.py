"""KeySequenceBuffer: the hand-rolled chord/digit-count state machine that
sits in front of the keymap registry.

Textual has no native multi-keystroke chord support, so every keypress is
routed through one path: on_key -> this buffer -> registry.resolve(). Pure
Python, no Textual dependency, synchronously testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from lifeos.adapters.tui.keymap import KeymapEntry, KeymapRegistry, Scope

FeedResultKind = Literal["matched", "waiting", "no_match"]


@dataclass(frozen=True)
class FeedResult:
    kind: FeedResultKind
    entry: KeymapEntry | None = None

    @classmethod
    def matched(cls, entry: KeymapEntry) -> "FeedResult":
        return cls(kind="matched", entry=entry)

    @classmethod
    def waiting(cls) -> "FeedResult":
        return cls(kind="waiting")

    @classmethod
    def no_match(cls) -> "FeedResult":
        return cls(kind="no_match")


@dataclass
class KeySequenceBuffer:
    registry: KeymapRegistry
    _pending: str = field(default="", init=False, repr=False)

    def feed(self, scope: Scope, key: str) -> FeedResult:
        """
        - a single digit '0'-'9', when nothing is pending, is consumed
          silently as part of a leading count and never reaches the
          registry (return waiting())
        - pending + key exactly matches a registered key in scope ->
          matched(entry), reset pending
        - pending + key is a strict prefix of some longer bound key in
          scope -> waiting(), keep accumulating
        - otherwise -> no_match(), reset pending (abandon whatever was
          pending)
        """
        if not self._pending and key.isdigit():
            return FeedResult.waiting()

        candidate = self._pending + key

        entry = self.registry.resolve(scope, candidate)
        if entry is not None:
            self.reset()
            return FeedResult.matched(entry)

        if self.registry.is_prefix(scope, candidate):
            self._pending = candidate
            return FeedResult.waiting()

        self.reset()
        return FeedResult.no_match()

    def reset(self) -> None:
        self._pending = ""
