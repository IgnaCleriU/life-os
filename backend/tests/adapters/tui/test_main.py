from __future__ import annotations

from lifeos.adapters.tui import __main__ as tui_main
from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.modules.stub import StubModule


def test_main_runs_a_shell_app_wired_to_the_stub_module(monkeypatch) -> None:  # noqa: ANN001
    captured: dict[str, object] = {}

    def fake_run(self: ShellApp) -> None:
        captured["app"] = self

    monkeypatch.setattr(ShellApp, "run", fake_run)

    tui_main.main()

    app = captured.get("app")
    assert isinstance(app, ShellApp)
    assert isinstance(app.module, StubModule)
