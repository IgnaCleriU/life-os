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
from uuid import UUID

import typer

from lifeos.domain import (
    DomainValidationError,
    ProjectNotEmpty,
    ProjectNotFound,
    TaskNotFound,
)

F = TypeVar("F", bound=Callable[..., Any])


class ProjectNameNotFound(Exception):
    """No existe ningún proyecto con el nombre buscado.

    Usado por `capture` para resolver un `#nombre` (o el fallback "inbox")
    a un id de proyecto antes de llamar al caso de uso.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"No project found with name '{name}'")


class AmbiguousProjectName(Exception):
    """Más de un proyecto activo comparte el nombre buscado."""

    def __init__(self, name: str, candidates: list[UUID]) -> None:
        self.name = name
        self.candidates = candidates
        candidate_ids = ", ".join(str(candidate) for candidate in candidates)
        super().__init__(
            f"Multiple projects named '{name}' found: {candidate_ids}. "
            "Use 'lifeos task create <project_id> ...' with an explicit "
            "id to disambiguate."
        )


_DOMAIN_ERROR_CODES: dict[type[Exception], str] = {
    DomainValidationError: "domain_validation_error",
    ProjectNotFound: "project_not_found",
    TaskNotFound: "task_not_found",
    ProjectNotEmpty: "project_not_empty",
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
