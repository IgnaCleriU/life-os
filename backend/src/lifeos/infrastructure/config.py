"""Carga de configuración de la app.

Lee variables de entorno (o un archivo `.env`) y las expone como un objeto
`Settings` tipado para el resto de infrastructure/adapters.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, poblada desde el entorno o `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Life OS"
    app_port: int = 8000
    database_url: str = "sqlite:///./lifeos.db"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) de la app."""
    return Settings()
