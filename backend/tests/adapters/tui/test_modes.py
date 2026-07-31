"""Tests for ModeController: the 5 ADR 0008 modes and the Esc rule.

Covers exactly what the ADR's "Modality" section requires: exactly one
mode is always active, starting in NORMAL; entering a non-NORMAL mode from
NORMAL; and `Esc` always going back exactly one level (never more, never
less, never with another side effect).
"""

from __future__ import annotations

import pytest

from lifeos.adapters.tui.modes import Mode, ModeController

NON_NORMAL_MODES = [Mode.INSERT, Mode.FILTER, Mode.SELECT, Mode.PALETTE]

# --- initial state -----------------------------------------------------------


def test_starts_in_normal_mode() -> None:
    controller = ModeController()
    assert controller.mode == Mode.NORMAL


# --- enter(): NORMAL -> non-NORMAL mode --------------------------------------


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_enter_transitions_from_normal_to_target_mode(mode: Mode) -> None:
    controller = ModeController()
    controller.enter(mode)
    assert controller.mode == mode


def test_enter_normal_is_a_no_op_since_it_is_already_the_default() -> None:
    # NORMAL is the base mode, not an "enterable" mode like the other four:
    # there's no key in the ADR that "enters NORMAL" (that's reached only
    # via escape()). Calling enter(NORMAL) explicitly shouldn't require
    # already being in NORMAL, nor become a special case: it's simply
    # treated as a valid transition to the default state.
    controller = ModeController()
    controller.enter(Mode.NORMAL)
    assert controller.mode == Mode.NORMAL


# --- enter(): deliberate decision on chaining non-NORMAL modes -------------


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_enter_from_a_non_normal_mode_is_rejected(mode: Mode) -> None:
    # Design decision (see ModeController.enter's docstring in modes.py):
    # you CANNOT chain from one non-NORMAL mode to another (e.g. FILTER ->
    # PALETTE) without passing through NORMAL first. The ADR models the
    # mode stack as depth 2 at most (NORMAL, and at most one mode above
    # it) — the only reading consistent with "Esc always goes back exactly
    # one level": if chaining were allowed, an Esc from the deeper mode
    # would be ambiguous (back to the previous mode, or straight to
    # NORMAL?), and the ADR never resolves that ambiguity because it
    # doesn't anticipate it. That's why enter() requires being in NORMAL
    # and raises ValueError in any other case, instead of silently
    # allowing a deeper stack that escape() couldn't correctly unwind.
    controller = ModeController()
    controller.enter(Mode.FILTER if mode != Mode.FILTER else Mode.SELECT)
    with pytest.raises(ValueError):
        controller.enter(mode)


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_enter_from_non_normal_mode_does_not_change_mode(mode: Mode) -> None:
    controller = ModeController()
    other_mode = Mode.PALETTE if mode != Mode.PALETTE else Mode.INSERT
    controller.enter(other_mode)
    with pytest.raises(ValueError):
        controller.enter(mode)
    assert controller.mode == other_mode


# --- escape(): the "exactly one level" rule ----------------------------------


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_escape_from_non_normal_mode_returns_true_and_lands_on_normal(
    mode: Mode,
) -> None:
    controller = ModeController()
    controller.enter(mode)
    handled = controller.escape()
    assert handled is True
    assert controller.mode == Mode.NORMAL


def test_escape_from_normal_returns_false_and_stays_normal() -> None:
    # From NORMAL, Esc isn't this controller's job (moving pane focus or
    # asking for quit confirmation are the shell's responsibilities, which
    # doesn't exist yet). The controller must return False so the caller
    # knows it has to handle it itself, and the mode must stay unchanged
    # (not silently "do something").
    controller = ModeController()
    handled = controller.escape()
    assert handled is False
    assert controller.mode == Mode.NORMAL


def test_escape_twice_in_a_row_only_handles_the_first_call() -> None:
    controller = ModeController()
    controller.enter(Mode.SELECT)

    first = controller.escape()
    second = controller.escape()

    assert first is True
    assert second is False
    assert controller.mode == Mode.NORMAL
