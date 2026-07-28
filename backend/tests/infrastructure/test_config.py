"""Tests de la configuración por defecto de la base de datos.

Lo que se protege acá es que la ruta por defecto **no** dependa del
directorio de trabajo: la API REST, el servidor MCP y la futura TUI son
procesos distintos, lanzados desde cwd distintos, y deben terminar en el
mismo archivo sin configurar nada.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from lifeos.infrastructure.config import Settings, default_database_url


class TestDefaultDatabaseUrl:
    def test_uses_xdg_data_home_when_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

        assert default_database_url() == "sqlite:////custom/data/life-os/lifeos.db"

    def test_falls_back_to_local_share(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setattr(
            Path, "home", classmethod(lambda cls: Path("/home/someone"))
        )

        expected = "sqlite:////home/someone/.local/share/life-os/lifeos.db"
        assert default_database_url() == expected

    def test_is_absolute_and_independent_of_cwd(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

        from_one_cwd = default_database_url()
        monkeypatch.chdir(tmp_path)
        from_another_cwd = default_database_url()

        assert from_one_cwd == from_another_cwd
        assert "://./" not in from_one_cwd


class TestSettings:
    def test_database_url_defaults_to_the_user_data_dir(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

        settings = Settings(_env_file=None)

        assert settings.database_url == "sqlite:////custom/data/life-os/lifeos.db"

    def test_environment_still_overrides_the_default(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./other.db")

        settings = Settings(_env_file=None)

        assert settings.database_url == "sqlite:///./other.db"


def test_default_does_not_depend_on_os_getcwd(monkeypatch: pytest.MonkeyPatch):
    """Guardarraíl explícito contra volver a una ruta relativa al cwd."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")

    def _boom() -> str:  # pragma: no cover - solo se ejecuta si hay regresión
        raise AssertionError("la ruta por defecto no debe consultar el cwd")

    monkeypatch.setattr(os, "getcwd", _boom)

    assert default_database_url().startswith("sqlite:////")
