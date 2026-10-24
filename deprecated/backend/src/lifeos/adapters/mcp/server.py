"""Servidor MCP (transporte stdio) que expone las tools de `tools.py` a
agentes de IA. Igual que `adapters/rest/main.py`, garantiza que el esquema
de la DB exista antes de atender pedidos (ver `create_db_and_tables`).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from lifeos.adapters.mcp.tools import register_tools
from lifeos.infrastructure.config import get_settings
from lifeos.infrastructure.db.session import create_db_and_tables


def create_server() -> FastMCP:
    """Construye y configura la instancia de FastMCP."""
    settings = get_settings()
    server = FastMCP(settings.app_name)
    register_tools(server)
    return server


mcp_server = create_server()


def main() -> None:
    """Punto de entrada del script `lifeos-mcp`: crea las tablas si no
    existen y sirve el servidor MCP por stdio.
    """
    create_db_and_tables()
    mcp_server.run(transport="stdio")


if __name__ == "__main__":
    main()
