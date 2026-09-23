"""Guardia local de la API REST (ADR 0009, spec 0002).

La API corre como daemon en `127.0.0.1` y la consume el overlay de Quickshell.
Escuchar solo en loopback no alcanza: cualquier página abierta en el navegador
puede apuntar a `localhost`. Dos chequeos lo cierran:

- **Token:** toda ruta salvo `/health` exige `Authorization: Bearer <token>`.
  Un header propio obliga al navegador a hacer un preflight CORS, y como la
  app no emite headers CORS, el preflight falla: una página no puede ni leer
  ni escribir.
- **Host:** solo se aceptan `localhost`, `127.0.0.1` y `::1`, lo que bloquea
  el DNS rebinding (un dominio del atacante que resuelve a 127.0.0.1).

Vive en el adapter REST porque es transporte, no negocio: MCP, CLI y TUI
abren la base en proceso y no pasan por acá.
"""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response

LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
OPEN_PATHS = frozenset({"/health"})


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    headers = (
        {"WWW-Authenticate": "Bearer"}
        if status_code == status.HTTP_401_UNAUTHORIZED
        else None
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


def _hostname(host_header: str) -> str | None:
    """Extrae el nombre de host de un header `Host` (con o sin puerto)."""
    try:
        return urlsplit(f"//{host_header}").hostname
    except ValueError:
        return None


def install_local_guard(app: FastAPI, *, api_token: str | None) -> None:
    """Registra el middleware de token + host en `app`.

    Con `api_token=None` la guardia sigue activa pero rechaza todo: es el
    caso de un `uvicorn` lanzado a mano sin token, y fallar cerrado es
    preferible a quedar abierto sin avisar.
    """

    @app.middleware("http")
    async def local_guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        if _hostname(request.headers.get("host", "")) not in LOOPBACK_HOSTS:
            return _error(
                status.HTTP_403_FORBIDDEN,
                "forbidden_host",
                "The API only answers requests addressed to localhost.",
            )

        if api_token is None:
            return _error(
                status.HTTP_401_UNAUTHORIZED,
                "unauthorized",
                "No API token is configured. Run lifeos-daemon, or set "
                "LIFEOS_API_TOKEN (or LIFEOS_API_AUTH=disabled for local "
                "development only).",
            )

        scheme, _, presented = request.headers.get("authorization", "").partition(
            " "
        )
        # Se comparan bytes: `compare_digest` con `str` lanza TypeError ante
        # caracteres no ASCII, y Starlette decodifica los headers como latin-1,
        # así que un header raro daría 500 en vez de 401.
        if scheme.lower() != "bearer" or not secrets.compare_digest(
            presented.strip().encode(), api_token.encode()
        ):
            return _error(
                status.HTTP_401_UNAUTHORIZED,
                "unauthorized",
                "Missing or invalid bearer token.",
            )

        return await call_next(request)
