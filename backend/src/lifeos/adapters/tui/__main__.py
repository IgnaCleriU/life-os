"""Dev-only manual entry point: `uv run python -m lifeos.adapters.tui`.

Not a packaged `[project.scripts]` console entry - that's `lifeos-tui`,
reserved for Step 13 once the real Projects/Tasks module replaces the stub.
This exists so the shell can actually be run and looked at in a terminal
during review, alongside the automated Pilot-driven tests.
"""

from __future__ import annotations

from lifeos.adapters.tui.app import ShellApp
from lifeos.adapters.tui.modules.stub import StubModule


def main() -> None:
    app = ShellApp(module=StubModule())
    app.run()


if __name__ == "__main__":
    main()
