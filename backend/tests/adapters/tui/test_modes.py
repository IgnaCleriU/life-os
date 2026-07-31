"""Tests de ModeController: las 5 modalidades del ADR 0008 y la regla de Esc.

Cubre exactamente lo que exige la sección "Modality" del ADR: siempre hay
un único modo activo, arrancando en NORMAL; entrar a un modo no-NORMAL
desde NORMAL; y `Esc` retrocediendo siempre un nivel exacto (nunca más,
nunca menos, nunca con otro efecto colateral).
"""

from __future__ import annotations

import pytest

from lifeos.adapters.tui.modes import Mode, ModeController

NON_NORMAL_MODES = [Mode.INSERT, Mode.FILTER, Mode.SELECT, Mode.PALETTE]

# --- estado inicial ---------------------------------------------------------


def test_starts_in_normal_mode() -> None:
    controller = ModeController()
    assert controller.mode == Mode.NORMAL


# --- enter(): NORMAL -> modo no-NORMAL --------------------------------------


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_enter_transitions_from_normal_to_target_mode(mode: Mode) -> None:
    controller = ModeController()
    controller.enter(mode)
    assert controller.mode == mode


def test_enter_normal_is_a_no_op_since_it_is_already_the_default() -> None:
    # NORMAL es el modo base, no un modo "entrable" como los otros cuatro:
    # no existe una tecla en el ADR que "entre a NORMAL" (a eso se llega
    # únicamente vía escape()). Llamar enter(NORMAL) explícitamente no debería
    # requerir estar ya en NORMAL ni convertirse en un caso especial: se trata
    # simplemente como una transición válida hacia el estado por defecto.
    controller = ModeController()
    controller.enter(Mode.NORMAL)
    assert controller.mode == Mode.NORMAL


# --- enter(): decisión deliberada sobre encadenar modos no-NORMAL ----------


@pytest.mark.parametrize("mode", NON_NORMAL_MODES)
def test_enter_from_a_non_normal_mode_is_rejected(mode: Mode) -> None:
    # Decisión de diseño (ver docstring de ModeController.enter en modes.py):
    # NO se puede encadenar de un modo no-NORMAL a otro (p. ej. FILTER ->
    # PALETTE) sin pasar por NORMAL primero. El ADR modela la pila de modos
    # como profundidad 2 como máximo (NORMAL, y a lo sumo un modo encima) —
    # es la única lectura consistente con "Esc siempre retrocede exactamente
    # un nivel": si se permitiera encadenar, un Esc desde el modo más
    # profundo sería ambiguo (¿vuelve al modo anterior o directo a NORMAL?),
    # y el ADR nunca resuelve esa ambigüedad porque no la contempla. Por eso
    # enter() exige estar en NORMAL y levanta ValueError en cualquier otro
    # caso, en vez de permitir silenciosamente una pila más profunda que
    # escape() no podría deshacer correctamente.
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


# --- escape(): la regla de "un nivel exacto" --------------------------------


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
    # Desde NORMAL, Esc no es resorte de este controller (mover el foco de
    # panel o pedir confirmación de salida son responsabilidades del shell,
    # que todavía no existe). El controller debe devolver False para que el
    # caller sepa que tiene que manejarlo él mismo, y el modo debe quedar
    # intacto (no "hace algo" silenciosamente).
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
