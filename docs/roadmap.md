# Life OS — Roadmap

This document is the single source of truth for project phasing and status.
For the product rationale behind these phases, see [vision.md](vision.md).
For architectural principles, see [../ARCHITECTURE.md](../ARCHITECTURE.md).

## Phases

| Phase | Name | Status |
|---|---|---|
| 0 | Foundations | In progress |
| 1 | MVP: Projects + Tasks | In progress |
| 2 | Notes + search | Planned |
| 3 | Calendar | Planned |
| 4 | Home inventory | Planned |
| 5 | Passwords / Vault | Planned |
| 6 | Android app | Planned |
| 7 | Hardening | Planned |

### Phase 0 — Foundations

- Monorepo structure with hexagonal architecture (ports and adapters). **Done.**
- Docker Compose local environment (backend service + SQLite volume). **Done.**
- Basic CI (commit-lint gate + ruff + pytest). **Done.**
- Base data model (users, JWT auth). **Resolved for the local case** by
  [adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md):
  one local user, no accounts, a per-install token on a loopback-only
  daemon (Step 14). Users and JWT return only if remote/multi-device
  access (Phase 6) is taken on.

### Phase 1 — MVP: Projects + Tasks

Full REST endpoints (CRUD for projects/tasks), a minimal frontend
(list + kanban), a basic CLI/TUI, and an MCP server exposing the tools
described in [vision.md](vision.md#agent-access-model), wired to
Claude Desktop/Code to validate the agent-to-API flow end to end.

Task breakdown and current status:

| Step | Scope | Status |
|---|---|---|
| 1. Scaffolding | Repo structure, `pyproject.toml`, Docker Compose, `Dockerfile`, `/health` endpoint | Done |
| 2. Domain | `Project`, `Task` entities, domain exceptions, domain unit tests | **Done** |
| 3. Ports | `ProjectRepository`, `TaskRepository` interfaces (`Protocol`) | **Done** |
| 4. Use cases | `CreateProject`, `ListProjects`, `CreateTask`, `ListTasks`, `UpdateTask`, `CompleteTask` + tests with in-memory fake repositories | **Done** |
| 5. Infrastructure (SQLite) | `ProjectORM`/`TaskORM` models, `SQLiteProjectRepository`, `SQLiteTaskRepository`, DB session | **Done** |
| 6. REST adapter | DTOs, dependency injection, routers for projects/tasks | **Done** |
| 7. MCP adapter | MCP server (stdio) and tools calling the same use cases as REST | **Done** |
| 8. MVP closing | Load the full roadmap (Phases 1-7) as a Project + Tasks inside the app itself, via the agent over MCP | Pending |
| 9. Lifecycle use cases | Soft deletion, project mutation, `doing`, move, get-by-id, filtered listings; WAL + `busy_timeout` | **Done** |
| 10. REST + MCP parity | Expose every Step 9 capability as routes and tools | **Done** |
| 11. CLI adapter | `adapters/cli/` (Typer): one command per use case, plus `adapters/shared/quick_add.py` (the `!high @sat #casa` parser) and a `capture`/`add` wrapper | **Done** |
| 12. TUI shell | `adapters/tui/`: generic Textual shell (panes, focus, modes, keymap registry + dispatch, palette, `?` overlay, undo/redo, status bar), built against a stub module so it stays free of Projects/Tasks code | **Done** |
| 13. TUI module + desktop wiring | `adapters/tui/modules/projects_tasks.py` implementing the shell's module contract, `lifeos-tui`/`lifeos-capture` console scripts, `docs/tui.md` with the Hyprland/Omarchy binds | **Done** |
| 14. REST as a local product surface | Token auth + `Host` check, `lifeos-daemon` (systemd `--user`), `GET /revision`, quick-add over REST with shared `#project` resolution | **Done** |
| 15. Quickshell board | `desktop/omarchy-plugin/` (Omarchy shell plugin `lifeos.board`): overlay with the TUI's panes, modes and keymap, plus mouse, live quick-add preview, live refresh and notifications | **Done** |

Steps 9-13 implement
[adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md).
They are ordered deliberately: the ADR makes the TUI the reference client, so
every capability it needs exists as a use case first and reaches REST and MCP
at the same time. Step 9 is therefore pure domain/application/infrastructure
work with no interface present.

Step 9 changes the SQLite schema (`deleted_at` on both tables). There is no
migration tooling yet, so an existing `~/.local/share/life-os/lifeos.db` must be
deleted and recreated — `create_all` does not add columns to existing tables.
**This destroys every project and task currently stored in it** — back up
the file first (or confirm with whoever owns the data) rather than treating
this as a routine step. Do this once, after Steps 9-10 land and before
using the CLI or TUI adapters built in the steps below.

**Steps 11-13 are strictly ordered** — each is one PR, and each consumes the
previous one's contract:

- **Step 11 (CLI)** is the first human-usable adapter and, being non-modal,
  the cheapest place to shake out the application-layer surface before the
  TUI is built on top of it. The quick-add parser it introduces
  (`adapters/shared/quick_add.py`) is shared with Step 13's TUI rather than
  duplicated, per ADR 0008.
- **Step 12 (TUI shell)** is deliberately built against a trivial stub
  module before any Projects/Tasks code exists, so the shell/module boundary
  the ADR mandates is real rather than aspirational. **It must first amend
  ADR 0008's keymap**: the accepted table binds both `d` (due date) and `dd`
  (delete) in the tasks pane, which collide — `d` is simultaneously a
  complete binding and a prefix of `dd`. Resolution: `dd` keeps delete; the
  due-date picker moves to `@`, mirroring the quick-add syntax that already
  teaches `@sat` as a due date. Amend the ADR's keymap table in this PR
  rather than opening a new one, and add a keymap-registry test asserting no
  binding is a strict prefix of another unless declared as such.
- **Step 13 (module + wiring)** replaces the stub module and adds the
  console scripts and example Omarchy keybindings. No installer and no
  desktop-app ADR — packaging stays out of scope, as decided when this work
  was planned.

Steps 14-15 implement
[adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md),
which makes a Quickshell overlay the primary interface in place of the
TUI (kept as a fallback); the full design and task breakdown are in
[specs/0002-quickshell-desktop-client.md](specs/0002-quickshell-desktop-client.md).
Step 14 is backend-only and lands first; Step 15 depends on it.

The domain layer (`backend/src/lifeos/domain/`), the application ports and
use cases (`backend/src/lifeos/application/`), the SQLite infrastructure
(`backend/src/lifeos/infrastructure/`), the REST adapter
(`backend/src/lifeos/adapters/rest/`), the MCP adapter
(`backend/src/lifeos/adapters/mcp/`), and the CLI adapter
(`backend/src/lifeos/adapters/cli/`, plus the quick-add parser shared with
the future TUI in `backend/src/lifeos/adapters/shared/`) implement Steps
1-11, each with its own test suite under `backend/tests/` (Steps 9-10
shipped in [PR #19](https://github.com/IgnaCleri/life-os/pull/19)). The
REST API, the MCP server (over stdio), and the `lifeos` CLI all expose the
full Projects/Tasks lifecycle — create, filtered listing, get by id,
partial update, every status transition (including `doing`), move, soft
delete and restore — calling the same use cases per ADR 0002, with
structured error responses for domain and validation errors on REST and
`<code>: <message>` on stderr for the CLI. See [mcp-setup.md](mcp-setup.md)
for the full MCP tool list and [cli.md](cli.md) for the full CLI command
reference and quick-add syntax.

Step 12 adds the generic TUI shell (`backend/src/lifeos/adapters/tui/`):
panes, focus, the 5 modes, a single keymap registry driving dispatch, the
command palette and `?` overlay, undo/redo, and a status bar, built and
tested against a throwaway stub module
(`adapters/tui/modules/stub.py`) so the shell/module boundary is real
rather than aspirational — the shell itself imports none of `application`,
`domain`, or `infrastructure`. ADR 0008's tasks-pane keymap was amended in
the same PR to resolve the `d`/`dd` collision described above.

Step 13 replaces the stub with the real
`adapters/tui/modules/projects_tasks.py`, wired through its own
`adapters/tui/deps.py` (mirroring the CLI's), and adds two module-agnostic
shell primitives the ADR's full keymap needed that Step 12 didn't build
yet: a yes/no confirm dialog and a pick-one-of-a-few-options picker, both
generic `ModalScreen`s reusable by any future module. The tasks pane's
quick-add reuses `adapters/shared/quick_add.py` verbatim, and its due-date
picker reuses the same parser rather than a second one. `E` (edit
description) and `y` (copy as markdown) use Textual's own `App.suspend()`
and `App.copy_to_clipboard()` — no new dependency for either. `lifeos-tui`
and `lifeos-capture` are now real console scripts (`lifeos-capture` is a
thin `sys.argv` wrapper delegating to the CLI's own `capture` command, per
the ADR); the dev-only `python -m lifeos.adapters.tui` entry point now
runs the real module instead of the stub. See [tui.md](tui.md) for the
full command/keymap reference.

**Definition of Done (MVP):** in a single conversation with Claude
connected to the local MCP server, it is possible to create a project and
load the roadmap phases as tasks under it, and then see those tasks
correctly through both the REST API and the MCP tools.

### Phase 2 — Notes + search

- Notes data model and endpoints.
- Cross-module search (projects + notes).
- Extend the MCP server with note-related tools.

### Phase 3 — Calendar

- Event model with recurrence.
- Calendar view in the frontend.
- Reminders via background jobs.

### Phase 4 — Home inventory

- Item model with locations and attachments (photos).
- Concrete use case: inventory for a secondary residence.

### Phase 5 — Passwords / Vault

- Integration with an external vault (see [adr/README.md](adr/README.md)
  for the storage approach) or a self-built vault.
- Define agent permission policy specifically for this module, per the
  default-deny principle in [vision.md](vision.md#agent-access-model).

### Phase 6 — Android app

- Can start in parallel with Phase 2/3 once the API is stable.
- Kotlin + Jetpack Compose consuming the same REST API.

### Phase 7 — Hardening

- Rate limiting, full audit logging of AI agent actions.
- Automated backups.
- End-to-end tests.

## Immediate next steps

Steps 9-15 are done — the Omarchy board (`lifeos.board`, over
`lifeos-daemon`) is the primary interface for Projects/Tasks, with the TUI,
the CLI, REST and MCP alongside it. The desktop-app direction is recorded in
[adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md),
superseding 0005.

1. Reach the Phase 1 Definition of Done (Step 8): load the roadmap phases
   as a Project + Tasks in a single Claude conversation over MCP, and
   confirm the same data is visible through REST. Independent of Steps
   14-15; can happen whenever convenient.
2. Try the board on the real desktop (`desktop/install.sh`, then the
   bind in [desktop.md](desktop.md)): the automated checks run it headless,
   but layer-shell focus, blur and notifications only show up on Omarchy.
   Then the bar widget and a standalone quick-capture popup, each in its
   own spec.
3. Iterate on this roadmap as phases complete and priorities shift.
