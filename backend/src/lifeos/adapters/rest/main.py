"""Punto de entrada de FastAPI.

Crea la instancia de la app y expone el endpoint `/health`. Los routers de
projects y tasks se incluirán a medida que se implementen los use cases.
"""

from __future__ import annotations

from fastapi import FastAPI

from lifeos.infrastructure.config import get_settings


def create_app() -> FastAPI:
    """Construye y configura la instancia de FastAPI."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Healthcheck del backend: valida que la app está viva."""
        return {"status": "ok"}

    return app


app = create_app()
