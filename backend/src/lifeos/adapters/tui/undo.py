"""Pila genérica de undo/redo para el shell TUI.

El ADR 0008 dice: "the adapter keeps the previous entity state for the
last N writes and replays the inverse call." Este módulo no sabe nada de
entidades ni del módulo (Projects/Tasks u otro) que las manipula: solo
almacena `UndoableWrite`s — closures de cero argumentos que el módulo
construye cerrando sobre su propio estado — y los reproduce en orden.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

UNDO_STACK_LIMIT = 20  # "the last N writes" — N no especificado por el ADR


@dataclass(frozen=True)
class UndoableWrite:
    """Un write reversible: descripción para status bar + par undo/redo."""

    description: str
    undo: Callable[[], None]
    redo: Callable[[], None]


class UndoStack:
    """Pila acotada de `UndoableWrite`s con semántica estándar de undo-tree.

    Un `push()` posterior a cualquier `undo()` descarta el historial de
    redo (sin "phantom redo" tras una acción nueva).
    """

    def __init__(self, limit: int = UNDO_STACK_LIMIT) -> None:
        self._done: deque[UndoableWrite] = deque(maxlen=limit)
        self._undone: list[UndoableWrite] = []

    def push(self, write: UndoableWrite) -> None:
        self._undone.clear()
        self._done.append(write)

    def undo(self) -> UndoableWrite | None:
        if not self._done:
            return None
        write = self._done.pop()
        write.undo()
        self._undone.append(write)
        return write

    def redo(self) -> UndoableWrite | None:
        if not self._undone:
            return None
        write = self._undone.pop()
        write.redo()
        self._done.append(write)
        return write
