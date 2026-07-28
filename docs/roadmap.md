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
- Base data model (users, JWT auth). **Pending** — blocked on the
  desktop-app ADR that will supersede
  [adr/0005-deployment-target.md](adr/0005-deployment-target.md). Whether
  JWT still fits is itself an open question for that ADR: it was chosen for
  a networked backend, which a local desktop app is not.

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
| 11. CLI adapter | `adapters/cli/` (Typer): one command per use case, plus `adapters/shared/quick_add.py` (the `!high @sat #casa` parser) and a `capture`/`add` wrapper | Pending |
| 12. TUI shell | `adapters/tui/`: generic Textual shell (panes, focus, modes, keymap registry + dispatch, palette, `?` overlay, undo/redo, status bar), built against a stub module so it stays free of Projects/Tasks code | Pending |
| 13. TUI module + desktop wiring | `adapters/tui/modules/projects_tasks.py` implementing the shell's module contract, `lifeos-tui`/`lifeos-capture` console scripts, `docs/tui.md` with the Hyprland/Omarchy binds | Pending |

Steps 9-13 implement
[adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md).
They are ordered deliberately: the ADR makes the TUI the reference client, so
every capability it needs exists as a use case first and reaches REST and MCP
at the same time. Step 9 is therefore pure domain/application/infrastructure
work with no interface present.

Step 9 changes the SQLite schema (`deleted_at` on both tables). There is no
migration tooling yet, so an existing `~/.local/share/life-os/lifeos.db` must be
deleted and recreated — `create_all` does not add columns to existing tables.
Do this once, after Steps 9-10 land and before using the CLI or TUI adapters
built in the steps below.

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

The domain layer (`backend/src/lifeos/domain/`), the application ports and
use cases (`backend/src/lifeos/application/`), the SQLite infrastructure
(`backend/src/lifeos/infrastructure/`), the REST adapter
(`backend/src/lifeos/adapters/rest/`), and the MCP adapter
(`backend/src/lifeos/adapters/mcp/`) implement Steps 1-10, each with its own
test suite under `backend/tests/` (Steps 9-10 are on
[PR #19](https://github.com/IgnaCleri/life-os/pull/19), pending merge). Both
the REST API and the MCP
server (over stdio) expose the full Projects/Tasks lifecycle — create,
filtered listing, get by id, partial update, every status transition
(including `doing`), move, soft delete and restore — calling the same use
cases per ADR 0002, with structured error responses for domain and
validation errors on REST. See [mcp-setup.md](mcp-setup.md) for the full tool
list and how to point an agent at it.

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

1. Merge the Steps 9-10 PR, then delete and recreate
   `~/.local/share/life-os/lifeos.db` (schema change, no migration tooling
   yet) before relying on any client.
2. Step 11: build `adapters/cli/` — a Typer command per use case, plus the
   shared quick-add parser and a `capture`/`add` wrapper.
3. Step 12: build the generic TUI shell in `adapters/tui/` against a stub
   module, amending ADR 0008's keymap table (`d`/`dd` collision, see above)
   in the same PR.
4. Step 13: replace the stub with the Projects/Tasks module, add the
   `lifeos-tui`/`lifeos-capture` console scripts, and document the Omarchy
   keybindings.
5. Reach the Phase 1 Definition of Done (Step 8): load the roadmap phases
   as a Project + Tasks in a single Claude conversation over MCP, and
   confirm the same data is visible through REST. Independent of Steps
   9-13; can happen whenever convenient.
6. Record the desktop-app direction as an ADR superseding
   [adr/0005-deployment-target.md](adr/0005-deployment-target.md): Life OS
   is being built as a native TUI desktop app for Omarchy that launches the
   backend and the TUI together, rather than a hosted backend. This
   conditions auth, packaging, and whether remote/multi-device access
   (Phase 6) stays in scope. Still deferred — Step 13 intentionally ships
   without it (console scripts and example keybinds only, no installer).
7. Iterate on this roadmap as phases complete and priorities shift.
