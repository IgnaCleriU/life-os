"""Caso de uso: obtener la revisión actual de los datos.

Lo consume el overlay de Quickshell (ADR 0009) para enterarse de escrituras
hechas por otros procesos —típicamente el agente vía MCP— sin volver a listar
todo en cada sondeo.
"""

from __future__ import annotations

from lifeos.application.ports import RevisionSource


class GetRevision:
    """Devuelve el token de revisión vigente."""

    def __init__(self, revision_source: RevisionSource) -> None:
        self._revision_source = revision_source

    def execute(self) -> str:
        """Devuelve la revisión actual; solo es comparable por igualdad."""
        return self._revision_source.current()
