"""Parser de quick-add para captura rápida de tareas (CLI/TUI).

Implementa la sintaxis definida en el ADR 0008 ("Quick-add syntax"):
un tokenizer de una sola pasada, por espacios en blanco (`str.split()`,
sin regex), que separa de una línea de texto libre los modificadores de
prioridad (`!low` `!med` `!high`), fecha límite (`@today` `@tomorrow`,
abreviaturas de día de semana o `@YYYY-MM-DD`) y proyecto (`#nombre`).

El resultado es un value object puro (`ParsedQuickAdd`) pensado para
alimentar directamente los argumentos de `CreateTask.execute`; el
dominio no tiene noción de esta sintaxis, y este módulo no importa nada
de `adapters/cli` ni de la capa de aplicación: el módulo de TUI (paso
13) reutiliza este mismo parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from lifeos.domain import Priority

_PRIORITY_TOKENS = {
    "!low": Priority.LOW,
    "!med": Priority.MEDIUM,
    "!high": Priority.HIGH,
}

_WEEKDAY_TOKENS = {
    "@mon": 0,
    "@tue": 1,
    "@wed": 2,
    "@thu": 3,
    "@fri": 4,
    "@sat": 5,
    "@sun": 6,
}


@dataclass(frozen=True)
class ParsedQuickAdd:
    """Resultado de parsear una línea de quick-add."""

    title: str
    priority: Priority
    due_date: date | None
    project_name: str | None


def _try_parse_due_date(token: str, today: date) -> date | None:
    """Intenta interpretar `token` como fecha; None si está mal formado.

    `@today` es la forma explícita de decir "hoy". Las abreviaturas de
    día de semana (`@mon`..`@sun`) siempre resuelven a la próxima
    ocurrencia ESTRICTAMENTE futura: si hoy es martes, `@tue` cae la
    semana que viene, no hoy mismo (delta = (target - today.weekday())
    % 7; si el resultado es 0 se usa 7).
    """
    if token == "@today":
        return today
    if token == "@tomorrow":
        return today + timedelta(days=1)
    if token in _WEEKDAY_TOKENS:
        target = _WEEKDAY_TOKENS[token]
        delta = (target - today.weekday()) % 7
        if delta == 0:
            delta = 7
        return today + timedelta(days=delta)

    iso_candidate = token[1:]
    try:
        return date.fromisoformat(iso_candidate)
    except ValueError:
        return None


def parse_quick_add(text: str, *, today: date | None = None) -> ParsedQuickAdd:
    """Parsea una línea de quick-add en sus componentes.

    `today` es un reloj inyectable (por defecto `date.today()`) para
    hacer determinista la resolución de fechas relativas en los tests.

    Reglas de degradación: cualquier token que empiece con `!`, `@`,
    `#` o `+` pero no matchee exactamente la sintaxis esperada (por
    ejemplo `!urgent`, `@whenever`, `@2026-13-45`, o un sigilo suelto
    como `!`/`@`/`#`/`+`) se conserva tal cual como texto literal del
    título, en vez de fallar. Si aparecen varios tokens del mismo tipo,
    gana el último (fast-capture: no hay error, se prioriza la
    velocidad de captura sobre la corrección estricta). Los tokens
    `+tag` se reconocen, se quitan del título y se descartan en
    silencio: el sigilo `+` queda reservado para tags futuros (ver ADR
    0008), por lo que acá no se agrega un campo `tags` (YAGNI).
    """
    if today is None:
        today = date.today()

    priority = Priority.MEDIUM
    due_date: date | None = None
    project_name: str | None = None
    title_tokens: list[str] = []

    for token in text.split():
        if token in _PRIORITY_TOKENS:
            priority = _PRIORITY_TOKENS[token]
            continue

        if token.startswith("@") and len(token) > 1:
            parsed_date = _try_parse_due_date(token, today)
            if parsed_date is not None:
                due_date = parsed_date
                continue
            title_tokens.append(token)
            continue

        if token.startswith("#") and len(token) > 1:
            project_name = token[1:]
            continue

        if token.startswith("+") and len(token) > 1:
            continue

        title_tokens.append(token)

    title = " ".join(title_tokens)

    return ParsedQuickAdd(
        title=title,
        priority=priority,
        due_date=due_date,
        project_name=project_name,
    )
