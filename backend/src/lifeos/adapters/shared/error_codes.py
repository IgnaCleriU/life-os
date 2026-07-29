"""Códigos de error compartidos por los adapters que exponen excepciones de
dominio como strings (CLI y MCP).

`DOMAIN_ERROR_CODES` cubre solo las excepciones de dominio comunes a ambos
adapters. Excepciones locales de un adapter (ej. `ProjectNameNotFound` y
`AmbiguousProjectName` del CLI) se agregan en el propio adapter, no acá.

REST no consume este mapa: registra un exception handler de FastAPI por
excepción, que además define el status code HTTP — un mecanismo distinto,
no una traducción a string.
"""

from __future__ import annotations

from lifeos.domain import (
    DomainValidationError,
    ProjectNotEmpty,
    ProjectNotFound,
    TaskNotFound,
)

DOMAIN_ERROR_CODES: dict[type[Exception], str] = {
    DomainValidationError: "domain_validation_error",
    ProjectNotFound: "project_not_found",
    TaskNotFound: "task_not_found",
    ProjectNotEmpty: "project_not_empty",
}
