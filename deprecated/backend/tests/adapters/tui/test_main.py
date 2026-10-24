from __future__ import annotations

from lifeos.adapters.tui import __main__ as tui_main
from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule


def test_main_runs_a_shell_app_wired_to_the_projects_tasks_module(
    monkeypatch,  # noqa: ANN001
) -> None:
    captured: dict[str, object] = {}

    def fake_run(self: ShellApp) -> None:
        captured["app"] = self

    monkeypatch.setattr(ShellApp, "run", fake_run)
    monkeypatch.setattr(tui_main, "create_db_and_tables", lambda: None)

    tui_main.main()

    app = captured.get("app")
    assert isinstance(app, ShellApp)
    assert isinstance(app.module, ProjectsTasksModule)


def test_main_ensures_the_db_schema_exists_before_running(monkeypatch) -> None:  # noqa: ANN001
    calls: list[str] = []
    monkeypatch.setattr(ShellApp, "run", lambda self: calls.append("run"))
    monkeypatch.setattr(
        tui_main, "create_db_and_tables", lambda: calls.append("create_db_and_tables")
    )

    tui_main.main()

    assert calls == ["create_db_and_tables", "run"]
