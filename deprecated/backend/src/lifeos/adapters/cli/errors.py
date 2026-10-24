"""Traducción de errores de dominio (y propios del CLI) a exit codes.

Análogo a `_DOMAIN_ERROR_CODES`/`_as_tool_error` de `adapters/mcp/tools.py`,
pero para el CLI: en vez de envolver en un `ToolError` de MCP, el decorador
`handle_domain_errors` imprime `<code>: <message>` por STDERR y sale con
código 1. Los errores de uso (argumentos mal formados, comandos inexistentes)
son responsabilidad de Click/typer y usan su propio exit code (2); este
decorador no los toca.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import typer

from lifeos.adapters.shared.capture_target import (
    AmbiguousProjectName,
    ProjectNameNotFound,
)
from lifeos.adapters.shared.error_codes import DOMAIN_ERROR_CODES

F = TypeVar("F", bound=Callable[..., Any])

__all__ = ["AmbiguousProjectName", "ProjectNameNotFound", "handle_domain_errors"]


_DOMAIN_ERROR_CODES: dict[type[Exception], str] = {
    **DOMAIN_ERROR_CODES,
    ProjectNameNotFound: "project_name_not_found",
    AmbiguousProjectName: "ambiguous_project_name",
}


def handle_domain_errors(func: F) -> F:
    """Atrapa los errores de dominio/CLI mapeados en `_DOMAIN_ERROR_CODES`.

    Imprime `<code>: <mensaje>` por STDERR y sale con código 1. No atrapa
    excepciones de uso de Click/typer (`typer.Exit`, `click.UsageError`,
    etc.): esas siguen su propio camino (exit code 2).
    """
    mapped_exceptions = tuple(_DOMAIN_ERROR_CODES)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except mapped_exceptions as exc:
            code = _DOMAIN_ERROR_CODES[type(exc)]
            typer.echo(f"{code}: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    return wrapper  # type: ignore[return-value]
