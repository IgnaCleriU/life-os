"""Punto de entrada del CLI (`lifeos`), vía typer.

Igual que `adapters/mcp/server.py`, garantiza que el esquema de la DB exista
antes de atender comandos (ver `create_db_and_tables`). El callback raíz
guarda el flag global `--json` en `ctx.obj` para que los subcomandos (que
agregan sus propios sub-apps de typer) decidan si emiten JSON o texto plano.
"""

from __future__ import annotations

import typer

from lifeos.adapters.cli.project_commands import project_app
from lifeos.infrastructure.db.session import create_db_and_tables

app = typer.Typer(help="Life OS command-line interface.")

# --- Placeholders --------------------------------------------------------
# Sub-app vacío, registrado solo para que `lifeos --help` liste el grupo
# `task`. Un agente posterior (Step 13) reemplaza este registro por su
# propio sub-app (`task_commands.py`), con los comandos reales. No agregar
# comandos acá.

task_app = typer.Typer(help="Manage tasks.")

app.add_typer(project_app, name="project", help="Manage projects.")
app.add_typer(task_app, name="task", help="Manage tasks.")


@app.callback()
def root(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON output instead of plain text.",
    ),
) -> None:
    """Life OS command-line interface."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


def main() -> None:
    """Punto de entrada del script `lifeos`: crea las tablas si no existen
    y despacha al app de typer.
    """
    create_db_and_tables()
    app()


if __name__ == "__main__":
    main()
