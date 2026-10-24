> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](./DEPRECATED.md).

# Architecture

Living document — updated as domain modules are added (Notes, Calendar,
Inventory, Passwords) or new adapters are introduced. It describes the
current state of the architecture. For phase status, see
[docs/roadmap.md](docs/roadmap.md); for the reasoning behind key decisions,
see [docs/adr/README.md](docs/adr/README.md).

## Principle: hexagonal architecture

The **domain** (entities and business rules) knows nothing about FastAPI,
SQLite, or MCP — it is pure Python. This is central to Life OS because the
MCP server and the REST API are two distinct "entry points" into the same
business logic: both must execute exactly the same use-case logic, without
duplicating it. When a new module is added or the database engine changes,
neither the domain nor the use cases are touched — only a new implementation
of an already-defined port is added or replaced.

## Dependency rule

Dependency arrows always point inward:

```
adapters (REST, MCP) ──► application (use cases) ──► domain (entities)
                                    ▲
infrastructure (DB) ────────────────┘ (implements the ports defined by application)
```

## Layers

| Layer | Responsibility | Does not depend on |
|---|---|---|
| `domain/` | Entities (`Project`, `Task`, ...) and domain exceptions | `sqlmodel`, `fastapi`, `mcp` |
| `application/ports/` | Interfaces (`Protocol`/`ABC`) defining persistence contracts, e.g. `ProjectRepository` | Concrete implementations |
| `application/use_cases/` | Business logic (`CreateProject`, `CompleteTask`, ...), receives repositories via constructor | `sqlmodel`, `fastapi`, `mcp` |
| `infrastructure/` | Concrete implementation of the ports (e.g. `SQLiteProjectRepository`), config, DB session | — |
| `adapters/rest/` | FastAPI: routers, Pydantic DTOs, dependency injection, the local guard (bearer token + loopback `Host`, `auth.py`), and `lifeos-daemon` (`daemon.py`), which serves it on `127.0.0.1` for the desktop client | Its own business logic (delegates to `application`) |
| `adapters/mcp/` | MCP server: each tool calls the same use case used by REST | Its own business logic (delegates to `application`) |
| `adapters/cli/` | Typer CLI (`lifeos`): one command per use case, plus a `capture`/`add` quick-add wrapper, its own `deps.py` and `--json`/plain-text serialization | Its own business logic (delegates to `application`) |
| `adapters/tui/` | Textual TUI: a generic shell (panes, focus, modes, keymap registry + dispatch, palette, `?` overlay, undo/redo, status bar) driving a pluggable `TuiModule`; `modules/projects_tasks.py` is the real one, `modules/stub.py` remains as the shell's own domain-agnostic test fixture | `application`, `domain`, `infrastructure` — the shell only knows the `TuiModule` contract; only `modules/projects_tasks.py` (not the shell itself) depends on `application` |
| `desktop/omarchy-plugin/` (QML, outside the Python package) | The primary human interface (ADR 0009): an Omarchy shell plugin that is a pure REST client of `lifeos-daemon` — the same use cases, reached over HTTP instead of in process | Any Python code; business logic (quick-add parsing and `#project` resolution are asked of the daemon) |
| `adapters/shared/` | Code shared across driver adapters that is not itself a use case — the quick-add tokenizer (`quick_add.py`), the `#project` capture-target rule (`capture_target.py`, which receives use cases as plain callables), both used by the CLI, the TUI's real module and REST's quick-add routes; and the domain-error-code map (`error_codes.py`, CLI, MCP, and the TUI's real module) | `application`, `infrastructure`, any single adapter |

## Folder structure

```
life-os/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── lifeos/
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── project.py          # Project entity (dataclass, no external deps)
│   │       │   ├── task.py             # Task entity
│   │       │   └── exceptions.py       # domain exceptions (e.g. TaskNotFound)
│   │       │
│   │       ├── application/
│   │       │   ├── ports/              # abstract interfaces (Protocol/ABC)
│   │       │   │   ├── project_repository.py
│   │       │   │   ├── task_repository.py
│   │       │   │   └── revision_source.py  # opaque "data changed" token (ADR 0009)
│   │       │   └── use_cases/          # un caso de uso por archivo
│   │       │       ├── create_project.py    list_projects.py
│   │       │       ├── get_project.py       update_project.py
│   │       │       ├── complete_project.py  archive_project.py
│   │       │       ├── activate_project.py
│   │       │       ├── delete_project.py    restore_project.py
│   │       │       ├── create_task.py       list_tasks.py
│   │       │       ├── get_task.py          update_task.py
│   │       │       ├── complete_task.py     start_task.py
│   │       │       ├── reopen_task.py       move_task.py
│   │       │       ├── delete_task.py       restore_task.py
│   │       │       └── get_revision.py
│   │       │
│   │       ├── infrastructure/
│   │       │   ├── config.py           # settings (pydantic-settings)
│   │       │   └── db/
│   │       │       ├── models.py       # SQLModel: ProjectORM, TaskORM
│   │       │       ├── session.py      # engine + sessionmaker
│   │       │       ├── revision.py     # RevisionSource via PRAGMA data_version
│   │       │       └── repositories/
│   │       │           ├── sqlite_project_repository.py   # implements ProjectRepository
│   │       │           └── sqlite_task_repository.py      # implements TaskRepository
│   │       │
│   │       └── adapters/
│   │           ├── rest/
│   │           │   ├── main.py         # FastAPI instance, includes routers
│   │           │   ├── auth.py         # local guard: bearer token + loopback Host
│   │           │   ├── daemon.py       # `lifeos-daemon`: token, daemon.json, 127.0.0.1
│   │           │   ├── deps.py         # dependency injection (repos, use cases)
│   │           │   ├── schemas.py      # Pydantic DTOs (request/response)
│   │           │   └── routers/
│   │           │       ├── projects.py
│   │           │       ├── tasks.py
│   │           │       ├── quick_add.py  # /quick-add/preview, /quick-add
│   │           │       └── sync.py       # /revision
│   │           ├── mcp/
│   │           │   ├── server.py       # MCP server (stdio)
│   │           │   └── tools.py        # defines tools, calling the same use cases
│   │           ├── cli/
│   │           │   ├── main.py             # `lifeos` entry point, root --json flag
│   │           │   ├── deps.py             # dependency injection (repos, use cases)
│   │           │   ├── project_commands.py # `lifeos project ...`
│   │           │   ├── task_commands.py    # `lifeos task ...`
│   │           │   ├── capture.py          # `lifeos capture`/`add`, inbox get-or-create
│   │           │   ├── errors.py           # domain errors → exit code 1, `<code>: <msg>`
│   │           │   └── serializers.py      # entity → dict/plain-text, shared by both modes
│   │           ├── tui/
│   │           │   ├── app.py          # ShellApp: disables Textual's own palette, pushes ShellScreen
│   │           │   ├── __main__.py     # `python -m lifeos.adapters.tui`, same target as `lifeos-tui`
│   │           │   ├── capture.py      # `lifeos-capture`: sys.argv shim delegating to the CLI
│   │           │   ├── deps.py         # dependency injection (repos, use cases), mirrors cli/deps.py
│   │           │   ├── keymap.py       # Scope, KeymapEntry, KeymapRegistry (+ collision check)
│   │           │   ├── dispatch.py     # KeySequenceBuffer: chords + digit-count handling
│   │           │   ├── module.py       # TuiModule protocol, PaneItem/PaneContents/DetailContents
│   │           │   ├── modes.py        # Mode enum, ModeController (Esc-back-one-level)
│   │           │   ├── undo.py         # UndoStack, UndoableWrite
│   │           │   ├── widgets/        # ContextPane, CollectionPane, DetailPane, StatusBar
│   │           │   ├── screens/        # ShellScreen, PaletteScreen, HelpScreen, ConfirmScreen, OptionsPickerScreen
│   │           │   └── modules/
│   │           │       ├── projects_tasks.py  # the real module
│   │           │       └── stub.py            # kept as the shell's own domain-agnostic test fixture
│   │           └── shared/
│   │               ├── quick_add.py    # `!high @sat #casa` tokenizer (CLI, TUI, REST)
│   │               ├── capture_target.py  # which project a capture lands in (CLI, TUI, REST)
│   │               └── error_codes.py  # domain exception → code string (CLI, MCP, and the TUI's real module)
│   │
│   └── tests/
│       ├── domain/
│       ├── application/
│       └── adapters/
│
└── docs/
    └── (planning documents)
```

**Implementation notes:**
- `domain/` does not import `sqlmodel`, `fastapi`, or `mcp`. Pure Python only
  (dataclasses/enums).
- `ports/` are interfaces (`Protocol` from `typing`, or `ABC`) that
  `application/use_cases` consumes without knowing the concrete
  implementation.
- `rest/deps.py` and `mcp/server.py` are the only places where the real
  implementation (SQLite) is wired to the use cases — manual dependency
  injection, without additional DI frameworks for now.

## Current implementation status

- **Implemented:** domain layer, application ports and use cases, SQLite
  infrastructure, the REST adapter, the MCP adapter, and the CLI adapter —
  under `backend/src/lifeos/domain/`, `application/`, `infrastructure/`,
  `adapters/rest/`, `adapters/mcp/`, and `adapters/cli/` respectively, each
  with its own test suite under `backend/tests/`. The application layer
  covers the full Projects/Tasks lifecycle (Step 9), including soft
  deletion and filtered listings, and REST, MCP and the CLI all expose all
  of it (Steps 10-11) — see [docs/mcp-setup.md](docs/mcp-setup.md) for the
  MCP tool list and [docs/cli.md](docs/cli.md) for the CLI command
  reference. The CLI's quick-add tokenizer lives in
  `adapters/shared/quick_add.py`, colocated outside any single adapter
  because the TUI (Step 13) will reuse it.
  Step 12 adds the generic TUI shell adapter under `adapters/tui/` — panes,
  focus, the 5 modes, the keymap registry and dispatch, the command palette
  and `?` overlay, undo/redo, and a status bar, built and tested against a
  throwaway stub module (`adapters/tui/modules/stub.py`, kept as the
  shell's own test fixture) so the shell itself stays free of Projects/Tasks
  code (it imports none of `application`, `domain`, or `infrastructure`).
  Step 13 adds the real module (`adapters/tui/modules/projects_tasks.py`),
  its own `deps.py`, two further generic shell primitives (a confirm
  dialog and an options picker), and the `lifeos-tui`/`lifeos-capture`
  console scripts — the TUI is now a fully working reference client
  exposing every Projects/Tasks capability REST, MCP, and the CLI already
  expose. See [docs/tui.md](docs/tui.md) for the full command/keymap
  reference.
- **Pending:** Phase 1 Step 8 (MVP closing) — see [docs/roadmap.md](docs/roadmap.md).

## Soft deletion

`Project` and `Task` carry a `deleted_at` timestamp; `DeleteTask` and
`DeleteProject` stamp it instead of removing rows, and `RestoreTask` /
`RestoreProject` clear it. Restoring a hard-deleted entity would be the one
genuinely expensive undo case, because `Task.create()` and `Project.create()`
generate their own identifiers — soft deletion turns it into a field flip.

**The exclusion filter lives in the repositories, not in the use cases.** Every
read path starts from a private `_live()` select that already excludes deleted
rows, so a new query method cannot forget it; `get(..., include_deleted=True)`
is the single escape hatch, used only by the restore use cases. A guard test in
`backend/tests/infrastructure/test_soft_delete_contract.py` fails if a
repository grows a public method that has not been audited for this.

Deleting a project does **not** cascade: `DeleteProject` raises
`ProjectNotEmpty` while the project still has live tasks. Cascading would make
restore responsible for remembering exactly which tasks it took down.

See [docs/roadmap.md](docs/roadmap.md) for the phased plan.

## MCP server

The MCP server **does not access the database directly**: it consumes the
same use cases exposed by the REST adapter. This guarantees that business
rules (validation, permissions, auditing) are always applied, regardless of
whether the action originated from an AI agent, the frontend, or the CLI.

The desktop client lives next to the backend, not inside it:

```
desktop/
├── omarchy-plugin/        # lifeos.board: Board.qml (entry), BoardView.qml, panes/, modals/, lib/*.js
├── tests/                 # node tests for lib/, TUI keymap fixture, qml/ headless harness
├── systemd/               # lifeos-daemon.service (template)
└── install.sh             # unit + plugin link + enable
```

## Where the data lives

Every entry point (REST, MCP, the CLI, and the TUI) is a separate
process, but they all read and write **one** database: by default
`$XDG_DATA_HOME/life-os/lifeos.db` — in practice
`~/.local/share/life-os/lifeos.db`. That path is deliberately absolute and
outside the repository, so it does not depend on the working directory a
process was launched from, nor on the checkout, branch or worktree it was
launched from. `DATABASE_URL` overrides it (tests and containers do).

Because every entry point converges on one file, concurrent access is the
normal case rather than an accident: the board, an MCP server spawned by an
agent, and a REST process can all hold it open at once. `session.py` therefore
sets `journal_mode=WAL` and a non-zero `busy_timeout` alongside
`foreign_keys=ON`, so contention waits instead of raising `database is locked`.
There is no push-style cross-process invalidation. Instead, `GET /revision`
(backed by `PRAGMA data_version` on a dedicated connection) exposes a token
that changes after any process commits, so a long-lived client like the
Quickshell board polls it and reloads only when something changed.

This matters architecturally: sharing the application layer is only half of
the guarantee above. Two adapters running the same use cases against two
different database files would still show the agent and the user different
worlds. See
[docs/adr/0007-shared-database-location.md](docs/adr/0007-shared-database-location.md).

## Maintaining this document

Update it when:
- A new domain module is added (Notes, Calendar, Inventory, Passwords —
  Phase 2+).
- A new entry-point adapter is added (e.g. an Android app talking directly
  to the API).
- SQLite is replaced by PostgreSQL, or an existing port changes.
- The location or ownership of the database file changes (see "Where the
  data lives").

Significant architectural decisions should also be recorded as an ADR — see
[docs/adr/README.md](docs/adr/README.md).
