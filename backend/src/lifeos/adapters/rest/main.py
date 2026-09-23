"""Punto de entrada de FastAPI.

Crea la instancia de la app, registra los exception handlers que traducen
excepciones de dominio (y de validación de FastAPI) a respuestas HTTP con
forma uniforme, e incluye los routers de projects y tasks.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from lifeos.adapters.rest.auth import install_local_guard
from lifeos.adapters.rest.routers import projects, quick_add, sync, tasks
from lifeos.adapters.shared.capture_target import (
    AmbiguousProjectName,
    ProjectNameNotFound,
)
from lifeos.domain import (
    DomainValidationError,
    ProjectNotEmpty,
    ProjectNotFound,
    TaskNotFound,
)
from lifeos.infrastructure.config import get_settings
from lifeos.infrastructure.db.session import create_db_and_tables


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Crea las tablas al arrancar si no existen (idempotente).

    No hay un mecanismo de migraciones todavía (ver adr/README.md); hasta que
    exista, este es el único lugar donde se garantiza que el esquema exista
    antes de servir requests.
    """
    create_db_and_tables()
    yield


def create_app(
    *, api_token: str | None = None, auth_enabled: bool | None = None
) -> FastAPI:
    """Construye y configura la instancia de FastAPI.

    Sin argumentos, la auth sale de la configuración (`LIFEOS_API_AUTH`,
    `LIFEOS_API_TOKEN`). `lifeos-daemon` pasa su propio token generado; los
    tests la apagan explícitamente con `auth_enabled=False`.
    """
    settings = get_settings()
    if auth_enabled is None:
        auth_enabled = settings.api_auth == "enabled"
    if api_token is None:
        api_token = settings.api_token
    app = FastAPI(title=settings.app_name, lifespan=_lifespan)
    if auth_enabled:
        install_local_guard(app, api_token=api_token)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Healthcheck del backend: valida que la app está viva."""
        return {"status": "ok"}

    @app.exception_handler(DomainValidationError)
    def handle_domain_validation_error(
        request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        """Invariante de dominio violada (ej. nombre/título vacío) -> 400."""
        return _error_response(
            status.HTTP_400_BAD_REQUEST, "domain_validation_error", str(exc)
        )

    @app.exception_handler(ProjectNotFound)
    def handle_project_not_found(
        request: Request, exc: ProjectNotFound
    ) -> JSONResponse:
        """Proyecto inexistente -> 404."""
        return _error_response(status.HTTP_404_NOT_FOUND, "project_not_found", str(exc))

    @app.exception_handler(TaskNotFound)
    def handle_task_not_found(request: Request, exc: TaskNotFound) -> JSONResponse:
        """Tarea inexistente -> 404."""
        return _error_response(status.HTTP_404_NOT_FOUND, "task_not_found", str(exc))

    @app.exception_handler(ProjectNotEmpty)
    def handle_project_not_empty(
        request: Request, exc: ProjectNotEmpty
    ) -> JSONResponse:
        """Se intenta borrar un proyecto con tareas vivas -> 409."""
        return _error_response(
            status.HTTP_409_CONFLICT, "project_not_empty", str(exc)
        )

    @app.exception_handler(ProjectNameNotFound)
    def handle_project_name_not_found(
        request: Request, exc: ProjectNameNotFound
    ) -> JSONResponse:
        """`#nombre` de quick-add sin proyecto que coincida -> 404."""
        return _error_response(
            status.HTTP_404_NOT_FOUND, "project_name_not_found", str(exc)
        )

    @app.exception_handler(AmbiguousProjectName)
    def handle_ambiguous_project_name(
        request: Request, exc: AmbiguousProjectName
    ) -> JSONResponse:
        """`#nombre` de quick-add que coincide con varios proyectos -> 409."""
        return _error_response(
            status.HTTP_409_CONFLICT, "ambiguous_project_name", str(exc)
        )

    @app.exception_handler(RequestValidationError)
    def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Error de validación del body/params -> 422, misma forma de error."""
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "request_validation_error",
            str(exc),
        )

    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(quick_add.router)
    app.include_router(sync.router)

    return app


app = create_app()
