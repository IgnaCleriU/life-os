"""Punto de entrada del CLI (`lifeos`), vía typer.

Igual que `adapters/mcp/server.py`, garantiza que el esquema de la DB exista
antes de atender comandos (ver `create_db_and_tables`). La llamada vive en
el callback raíz, no en `main()`: Click resuelve `--help` en el comando raíz
sin invocar el callback del grupo, así que `lifeos --help` (sin subcomando)
nunca paga el costo de tocar la DB. Un `--help` en un subcomando (ej.
`lifeos project --help`) sí lo paga, porque Click igual despacha a través
del callback raíz antes de resolver el subgrupo — solo el caso `lifeos
--help` desnudo se beneficia. El callback también guarda el flag global
`--json` en `ctx.obj` para que los subcomandos (que agregan sus propios
sub-apps de typer) decidan si emiten JSON o texto plano.
"""

from __future__ import annotations

import typer

from lifeos.adapters.cli.capture import capture
from lifeos.adapters.cli.project_commands import project_app
from lifeos.adapters.cli.task_commands import task_app
from lifeos.infrastructure.db.session import create_db_and_tables

app = typer.Typer(help="Life OS command-line interface.")

app.add_typer(project_app, name="project", help="Manage projects.")
app.add_typer(task_app, name="task", help="Manage tasks.")
app.command("capture")(capture)
app.command("add")(capture)


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
    create_db_and_tables()
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


def main() -> None:
    """Punto de entrada del script `lifeos`: despacha al app de typer."""
    app()


if __name__ == "__main__":
    main()
