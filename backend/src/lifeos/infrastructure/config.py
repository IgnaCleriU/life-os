"""Carga de configuración de la app.

Lee variables de entorno (o un archivo `.env`) y las expone como un objeto
`Settings` tipado para el resto de infrastructure/adapters.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_database_url() -> str:
    """DB por defecto en el directorio de datos del usuario (spec XDG).

    Una ruta relativa al cwd (`sqlite:///./lifeos.db`) haría que cada
    cliente termine con su propia base según desde dónde se lo lance: el
    servidor MCP, la API REST y la futura TUI son procesos distintos y no
    comparten directorio de trabajo. Anclarla a `XDG_DATA_HOME` les da a
    todos el mismo archivo sin depender de variables de entorno.
    """
    data_home = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return f"sqlite:///{Path(data_home) / 'life-os' / 'lifeos.db'}"


class Settings(BaseSettings):
    """Configuración de la aplicación, poblada desde el entorno o `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Life OS"
    app_port: int = 8000
    database_url: str = Field(default_factory=default_database_url)
    # Auth de la API REST (ADR 0009): encendida por defecto. Solo los tests y
    # las corridas ad-hoc de uvicorn la apagan, y de forma explícita.
    api_auth: Literal["enabled", "disabled"] = Field(
        default="enabled", validation_alias="LIFEOS_API_AUTH"
    )
    # Token para una corrida manual; `lifeos-daemon` genera el suyo propio.
    api_token: str | None = Field(default=None, validation_alias="LIFEOS_API_TOKEN")


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) de la app."""
    return Settings()
