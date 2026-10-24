"""Dev-only manual entry point: `uv run python -m lifeos.adapters.tui`.

Also the target of the packaged `lifeos-tui` console script (see
`backend/pyproject.toml`) - both run the same `main()`.
"""

from __future__ import annotations

from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.modules.projects_tasks import ProjectsTasksModule
from lifeos.infrastructure.db.session import create_db_and_tables


def main() -> None:
    create_db_and_tables()
    app = ShellApp(module=ProjectsTasksModule())
    app.run()


if __name__ == "__main__":
    main()
