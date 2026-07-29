"""Emisión de resultados de comandos según el flag global `--json`.

Separado de `serializers.py` a propósito: ese módulo es pura serialización
(dataclass de dominio -> dict/str, sin `typer`); acá vive la capa que decide
*dónde* va ese resultado (stdout, JSON o texto plano) según `ctx.obj["json"]`
seteado por el callback raíz de `main.py`. Usado por `project_commands.py`,
`task_commands.py` y `capture.py` para no reimplementar el mismo
`if ctx.obj["json"]: ... else: ...` en cada uno.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TypeVar

import typer

T = TypeVar("T")


def emit_single(
    ctx: typer.Context,
    entity: T,
    dict_fn: Callable[[T], dict],
    format_fn: Callable[[T], str],
) -> None:
    """Emite una única entidad: JSON si `--json`, texto plano si no."""
    if ctx.obj["json"]:
        typer.echo(json.dumps(dict_fn(entity)))
    else:
        typer.echo(format_fn(entity))


def emit_many(
    ctx: typer.Context,
    entities: list[T],
    dict_fn: Callable[[T], dict],
    format_fn: Callable[[list[T]], str],
) -> None:
    """Emite una lista de entidades.

    En modo texto plano, una lista vacía no imprime nada (a diferencia del
    modo JSON, que siempre imprime el array, vacío o no).
    """
    if ctx.obj["json"]:
        typer.echo(json.dumps([dict_fn(entity) for entity in entities]))
    elif entities:
        typer.echo(format_fn(entities))
