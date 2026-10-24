"""Puerto de revisión de datos.

Expone un token opaco que cambia cada vez que *cualquier* proceso confirma una
escritura en el almacenamiento compartido (ADR 0007): la API REST, el servidor
MCP, el CLI o la TUI. Los clientes que muestran datos en vivo (el overlay de
Quickshell, ADR 0009) lo consultan barato y solo vuelven a pedir los datos
cuando cambia.

El valor no tiene significado fuera de la comparación por igualdad: no es un
contador ordenado ni sobrevive necesariamente a un reinicio del proceso.
"""

from __future__ import annotations

from typing import Protocol


class RevisionSource(Protocol):
    """Contrato para obtener la revisión actual de los datos."""

    def current(self) -> str:
        """Devuelve el token de revisión vigente."""
        ...
