"""Tests de `UndoStack`/`UndoableWrite` (adapters/tui/undo.py).

Pila genérica de closures: no conoce entidades ni el módulo que las
construye, solo guarda pares (undo, redo) y los reproduce. Sin Textual,
sin DB — objetos mutables simples (listas) cerrados por los closures para
poder afirmar *cuál* closure corrió, no solo que corrió alguno.
"""

from __future__ import annotations

from lifeos.adapters.tui.undo import UndoableWrite, UndoStack


def _make_write(log: list[str], description: str = "write") -> UndoableWrite:
    """Crea un UndoableWrite cuyos closures registran su ejecución en `log`."""
    return UndoableWrite(
        description=description,
        undo=lambda: log.append(f"undo:{description}"),
        redo=lambda: log.append(f"redo:{description}"),
    )


def test_undo_calls_the_undo_closure_and_returns_the_write():
    log: list[str] = []
    write = _make_write(log, "delete task")
    stack = UndoStack()
    stack.push(write)

    result = stack.undo()

    assert log == ["undo:delete task"]
    assert result is write


def test_undo_then_redo_round_trips_and_write_is_undoable_again():
    log: list[str] = []
    write = _make_write(log, "delete task")
    stack = UndoStack()
    stack.push(write)

    stack.undo()
    redo_result = stack.redo()

    assert log == ["undo:delete task", "redo:delete task"]
    assert redo_result is write

    # El write volvió al lado "done": un undo() subsiguiente debe encontrarlo
    # de nuevo y llamar a su .undo una segunda vez.
    undo_result = stack.undo()

    assert log == ["undo:delete task", "redo:delete task", "undo:delete task"]
    assert undo_result is write


def test_undo_on_empty_stack_returns_none_and_does_not_raise():
    stack = UndoStack()

    assert stack.undo() is None


def test_redo_with_nothing_undone_returns_none_and_does_not_raise():
    log: list[str] = []
    stack = UndoStack()
    stack.push(_make_write(log, "delete task"))

    # Nada fue deshecho todavía, así que no hay historial de redo.
    assert stack.redo() is None


def test_push_after_undo_clears_the_redo_branch():
    log: list[str] = []
    write_a = _make_write(log, "a")
    write_b = _make_write(log, "b")
    write_c = _make_write(log, "c")
    stack = UndoStack()

    stack.push(write_a)
    stack.push(write_b)
    stack.undo()  # b deshecho, redo-disponible = [b]
    stack.push(write_c)

    # El push de c debe invalidar el historial de redo de b: no debe
    # resucitarlo silenciosamente.
    assert stack.redo() is None
