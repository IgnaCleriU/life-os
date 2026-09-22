# 0008. Keyboard-driven TUI adapter

- Status: Accepted — amended by [0009](0009-quickshell-desktop-client.md)
- Date: 2026-07
- Spec: [specs/0001-keyboard-driven-tui-adapter.md](../specs/0001-keyboard-driven-tui-adapter.md)

## Context

Life OS had two entry points into the application layer — REST and MCP (see
[0002-mcp-consumes-use-cases.md](0002-mcp-consumes-use-cases.md)) — and
neither is usable as a day-to-day human interface: REST needs a client, MCP
requires an agent conversation. Phase 1 of [../roadmap.md](../roadmap.md)
calls for a "basic CLI/TUI", and [0006-tech-stack.md](0006-tech-stack.md)
already picked Typer and Textual for it. Life OS targets one self-hosted
user on their own machine ([0005-deployment-target.md](0005-deployment-target.md)
was deprecated for framing this as a hosting question), on Omarchy
(Hyprland) — a keyboard-first environment. The application layer's use-case
surface was also missing most lifecycle operations (delete, project
mutation, move, `doing`, get-by-id, filtered listing) the interface would
need. See the spec for the full context.

## Decision

Add a keyboard-driven desktop client as a new adapter, `adapters/tui/`,
accompanied by a non-interactive `adapters/cli/` entry point. Both are
drivers of the application layer and, exactly as in ADR 0002, contain no
business logic of their own: they translate between keystrokes (or CLI
arguments) and use cases, calling them **in process** (no HTTP) rather than
through the REST API. The TUI is the reference client: every capability the
system has for Projects and Tasks must be reachable from it, so each
capability is added as a use case first and REST/MCP gain it for free.

This covers the client interface only — the board, its keymap, and how it
reaches the application layer. Packaging/launch, auth, and remote/
multi-device access remain open for the desktop-app ADR that supersedes
0005. See the spec for the full design (UI, modality, keymap, quick-add
syntax, undo, DB configuration) and the implementation task breakdown.

## Consequences

- Life OS becomes usable without an agent or an HTTP client.
- The required application-layer work (delete, project mutation, `doing`,
  move, get-by-id, filtered listing) closes real gaps in REST and MCP too,
  since all three share it.
- Treating the TUI as the reference client makes feature parity across
  adapters the default rather than an aspiration.
- Running in process against SQLite means the client cannot reach data on
  another machine — consistent with a desktop app, but it leaves
  multi-device access (the Android app, Phase 6) for a later ADR.
- Multiple processes now hold the same SQLite file open routinely (board +
  MCP + REST), which requires WAL and a non-zero `busy_timeout` to avoid
  `database is locked` errors.
- Soft deletion adds a `deleted_at` filter that every repository read path
  must apply — forgetting it surfaces deleted records.
- A modal, vim-style interface trades discoverability for speed; the
  command palette and `?` overlay are the mandatory mitigation.
- **Amended by ADR 0009:** the TUI is no longer the reference client — a
  Quickshell overlay reaching the use cases over a local REST daemon is
  the primary interface, and the TUI stays as an in-process fallback. The
  rule that every capability is a use case first still holds.
- **Amended in Step 12:** the originally accepted tasks-pane keymap bound
  both `d` (due date) and `dd` (delete), which collide. `dd` keeps delete;
  due date moved to `@`. See the spec for the corrected table.

## Alternatives considered

- **Web frontend as the first human interface** — deferred, not rejected;
  needs a running REST server and doesn't fit a keyboard-first desktop
  target.
- **Routing the TUI through HTTP** — rejected; reuse already lives at the
  use-case layer (ADR 0002), so HTTP would add a transport and a dependency
  on a running server with no reuse benefit.
- **CLI only, no TUI** — cheaper, but triage over a task list is poorly
  served by re-running commands and re-reading output.
- **Non-modal TUI** — simpler, but forecloses counts, bulk selection, and
  an unambiguous `Esc`.
- **Hard deletion, no undo** — smallest backend, but unrecoverable in a
  system holding personal data.
- **Tags and subtasks in this step** — deferred; subtasks alone turn the
  collection pane into a tree, a large scope increase for an unproven
  interface.
