"""Modalidad del shell TUI: los 5 modos del ADR 0008 y la regla de Esc.

Python puro, sin dependencia de `textual` — ver la sección "Modality" de
`docs/adr/0008-keyboard-driven-tui-adapter.md`. Este módulo solo sabe "qué
modo está activo" y "si Esc retrocedió un nivel o no"; todo lo demás (foco de
panel, confirmación de salida, qué implica *cerrar* un modo — p. ej. limpiar
el texto de un filtro) es responsabilidad de quien posea ese estado (el
shell), no de este controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(str, Enum):
    """Los 5 modos del shell. Siempre hay exactamente uno activo."""

    NORMAL = "normal"
    INSERT = "insert"
    FILTER = "filter"
    SELECT = "select"
    PALETTE = "palette"


@dataclass
class ModeController:
    """Controla la transición entre modos y la regla de Esc del ADR.

    El ADR modela la pila de modos con una profundidad máxima de 2: NORMAL
    (el nivel base) y, a lo sumo, un modo por encima de él. Es la única
    lectura consistente con "Esc siempre retrocede exactamente un nivel":
    si se permitiera encadenar de un modo no-NORMAL a otro (p. ej. FILTER ->
    PALETTE), un Esc desde el modo más profundo sería ambiguo (¿vuelve al
    modo anterior o directo a NORMAL?), y el ADR nunca resuelve esa
    ambigüedad porque no la contempla.
    """

    mode: Mode = Mode.NORMAL

    def enter(self, mode: Mode) -> None:
        """Transiciona a `mode`, solo permitido desde NORMAL.

        Encadenar entre dos modos no-NORMAL sin pasar por NORMAL (vía
        `escape()`) está deliberadamente prohibido — ver el docstring de la
        clase. Llamar `enter()` estando ya en un modo no-NORMAL levanta
        `ValueError` en lugar de sobrescribir el modo silenciosamente, para
        que cualquier intento de encadenar falle ruidosamente en el punto
        exacto que lo causó.

        `enter(Mode.NORMAL)` es válido siempre: no es un modo "entrable" en
        el sentido del ADR (no hay tecla que "entre a NORMAL", a eso se
        llega vía `escape()`), pero tratarlo como caso especial agregaría
        una rama sin beneficio real, dado que ya es el valor por defecto.
        """
        if self.mode is not Mode.NORMAL and mode is not Mode.NORMAL:
            raise ValueError(
                f"cannot enter {mode} directly from {self.mode}; "
                "escape() back to NORMAL first"
            )
        self.mode = mode

    def escape(self) -> bool:
        """Aplica la regla "Esc retrocede exactamente un nivel".

        Devuelve True si esta llamada cambió el modo (estábamos en un modo
        no-NORMAL y ahora estamos en NORMAL), False si ya estábamos en
        NORMAL — en cuyo caso el caller (el shell, más adelante) es quien
        debe manejar el comportamiento de Esc en NORMAL (foco de panel /
        prompt de salida), que este controller no implementa.
        """
        if self.mode is Mode.NORMAL:
            return False
        self.mode = Mode.NORMAL
        return True
