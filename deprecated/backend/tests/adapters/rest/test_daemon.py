"""Tests de `lifeos-daemon`: archivo de descubrimiento y arranque.

`uvicorn.run` se reemplaza por un doble: lo que interesa es qué app, host y
puerto recibe, y el ciclo de vida del archivo alrededor de esa llamada.
"""

from __future__ import annotations

import json
import socket
import stat
from pathlib import Path

import pytest

from lifeos.adapters.rest import daemon
from lifeos.infrastructure.config import get_settings


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_runtime_dir_uses_xdg_runtime_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))

    assert daemon.discovery_file() == tmp_path / "life-os" / "daemon.json"


def test_runtime_dir_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert daemon.runtime_dir() == tmp_path / ".local/state/life-os/run"


def test_discovery_file_is_private_and_complete(tmp_path: Path) -> None:
    path = tmp_path / "life-os" / "daemon.json"

    daemon.write_discovery_file(path, port=8123, token="tok")

    assert _mode(path.parent) == 0o700
    assert _mode(path) == 0o600
    content = json.loads(path.read_text())
    assert content["base_url"] == "http://127.0.0.1:8123"
    assert content["port"] == 8123
    assert content["token"] == "tok"
    assert isinstance(content["pid"], int)


def test_discovery_file_replaces_a_stale_one(tmp_path: Path) -> None:
    path = tmp_path / "daemon.json"
    daemon.write_discovery_file(path, port=1, token="old")

    daemon.write_discovery_file(path, port=2, token="new")

    assert json.loads(path.read_text())["token"] == "new"
    assert not path.with_suffix(".tmp").exists()


def test_remove_only_deletes_its_own_file(tmp_path: Path) -> None:
    path = tmp_path / "daemon.json"
    daemon.write_discovery_file(path, port=1, token="other-instance")

    daemon.remove_discovery_file(path, token="mine")
    assert path.exists()

    daemon.remove_discovery_file(path, token="other-instance")
    assert not path.exists()


def test_remove_tolerates_a_missing_file(tmp_path: Path) -> None:
    daemon.remove_discovery_file(tmp_path / "daemon.json", token="x")


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class TestMain:
    @pytest.fixture(autouse=True)
    def _env(self, monkeypatch, tmp_path: Path):
        self.port = _free_port()
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
        monkeypatch.setenv("APP_PORT", str(self.port))
        monkeypatch.setenv("LIFEOS_API_AUTH", "disabled")  # el daemon lo ignora
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()

    def _file(self, tmp_path: Path) -> dict:
        return json.loads((tmp_path / "life-os" / "daemon.json").read_text())

    def test_serves_on_loopback_with_a_guarded_app(self, monkeypatch, tmp_path):
        calls = {}

        def fake_serve(app, sock):
            calls.update(
                app=app, address=sock.getsockname(), file=self._file(tmp_path)
            )

        monkeypatch.setattr(daemon, "serve", fake_serve)

        daemon.main()

        assert calls["address"] == ("127.0.0.1", self.port)
        assert calls["file"]["port"] == self.port
        assert len(calls["file"]["token"]) >= 32

        from fastapi.testclient import TestClient

        client = TestClient(calls["app"], base_url=f"http://127.0.0.1:{self.port}")
        assert client.get("/projects").status_code == 401
        assert client.get("/health").status_code == 200

    def test_removes_the_file_on_exit_even_after_a_crash(self, monkeypatch, tmp_path):
        def crash(app, sock):
            raise RuntimeError("boom")

        monkeypatch.setattr(daemon, "serve", crash)

        with pytest.raises(RuntimeError):
            daemon.main()

        assert not (tmp_path / "life-os" / "daemon.json").exists()

    def test_a_second_instance_does_not_clobber_the_running_one(
        self, monkeypatch, tmp_path
    ):
        """Con el puerto tomado, la segunda instancia falla antes de escribir."""
        running = daemon.bind_socket(self.port)
        path = tmp_path / "life-os" / "daemon.json"
        daemon.write_discovery_file(path, port=self.port, token="running-token")
        monkeypatch.setattr(daemon, "serve", lambda app, sock: None)
        try:
            with pytest.raises(OSError):
                daemon.main()
        finally:
            running.close()

        assert self._file(tmp_path)["token"] == "running-token"

    def test_each_start_rotates_the_token(self, monkeypatch, tmp_path):
        tokens = []

        def fake_serve(app, sock):
            tokens.append(self._file(tmp_path)["token"])

        monkeypatch.setattr(daemon, "serve", fake_serve)

        daemon.main()
        daemon.main()

        assert tokens[0] != tokens[1]
