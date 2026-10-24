"""`lifeos-capture`: a thin wrapper over the CLI's capture command, meant to
be invoked from a window-manager launcher (Walker/dmenu) with the typed
text as argv - the highest-frequency action costs no window and no
context switch. Per ADR 0008: "It is a thin wrapper over the CLI."
"""

from __future__ import annotations

import sys

from lifeos.adapters.cli.main import main as cli_main


def main() -> None:
    sys.argv = [sys.argv[0], "capture", *sys.argv[1:]]
    cli_main()


if __name__ == "__main__":
    main()
