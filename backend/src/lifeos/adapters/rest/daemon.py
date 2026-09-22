"""`lifeos-daemon`: la API REST como proceso de fondo del escritorio (ADR 0009).

Lo lanza la unidad `systemd --user` de `desktop/systemd/`. En cada arranque:

1. Genera un token aleatorio nuevo.
2. Escribe `$XDG_RUNTIME_DIR/life-os/daemon.json` con la URL, el puerto y el
   token, en un directorio `0700` y un archivo `0600`. El runtime dir es un
   tmpfs del usuario que se borra al cerrar sesión, así que el token no
   sobrevive a la sesión. El overlay de Quickshell lee este archivo para
   saber a dónde y con qué credencial hablar.
3. Sirve la app solo en `127.0.0.1`, con la guardia local siempre encendida
   (ignora `LIFEOS_API_AUTH`).

Al salir borra el archivo, pero solo si sigue siendo el suyo: si otra
instancia ya lo reemplazó, no se lo pisa.
"""

from __future__ import annotations

import json
import os
import secrets
import signal
from pathlib import Path

import uvicorn

from lifeos.adapters.rest.main import create_app
from lifeos.infrastructure.config import get_settings

HOST = "127.0.0.1"
DISCOVERY_FILE_NAME = "daemon.json"


def runtime_dir() -> Path:
    """Directorio de runtime del usuario para Life OS.

    `XDG_RUNTIME_DIR` existe en cualquier sesión de systemd; el fallback bajo
    `~/.local/state` solo cubre entornos sin él (contenedores, SSH mínimos).
    """
    base = os.environ.get("XDG_RUNTIME_DIR")
    if base:
        return Path(base) / "life-os"
    return Path.home() / ".local" / "state" / "life-os" / "run"


def discovery_file() -> Path:
    return runtime_dir() / DISCOVERY_FILE_NAME


def write_discovery_file(path: Path, *, port: int, token: str) -> None:
    """Escribe el archivo de descubrimiento de forma atómica y privada."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    payload = {
        "base_url": f"http://{HOST}:{port}",
        "port": port,
        "token": token,
        "pid": os.getpid(),
    }
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(payload, handle)
    tmp.chmod(0o600)
    os.replace(tmp, path)


def remove_discovery_file(path: Path, *, token: str) -> None:
    """Borra el archivo si todavía describe a esta instancia."""
    try:
        current = json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return
    if current.get("token") == token:
        path.unlink(missing_ok=True)


def _exit_on_sigterm(signum: int, frame: object) -> None:
    raise SystemExit(0)


def main() -> None:
    """Punto de entrada del console script `lifeos-daemon`."""
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    path = discovery_file()
    app = create_app(api_token=token, auth_enabled=True)

    # uvicorn atrapa SIGTERM para cerrar ordenado y, al terminar, restaura el
    # handler previo y vuelve a emitir la señal. Con el handler por defecto
    # eso mata el proceso antes del `finally`; con este, sale limpio y el
    # archivo se borra (systemd detiene la unidad con SIGTERM).
    signal.signal(signal.SIGTERM, _exit_on_sigterm)
    write_discovery_file(path, port=settings.app_port, token=token)
    try:
        uvicorn.run(app, host=HOST, port=settings.app_port)
    finally:
        remove_discovery_file(path, token=token)


if __name__ == "__main__":
    main()
