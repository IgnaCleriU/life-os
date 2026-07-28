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
| `adapters/rest/` | FastAPI: routers, Pydantic DTOs, dependency injection | Its own business logic (delegates to `application`) |
| `adapters/mcp/` | MCP server: each tool calls the same use case used by REST | Its own business logic (delegates to `application`) |

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
│   │       │   │   └── task_repository.py
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
│   │       │       └── delete_task.py       restore_task.py
│   │       │
│   │       ├── infrastructure/
│   │       │   ├── config.py           # settings (pydantic-settings)
│   │       │   └── db/
│   │       │       ├── models.py       # SQLModel: ProjectORM, TaskORM
│   │       │       ├── session.py      # engine + sessionmaker
│   │       │       └── repositories/
│   │       │           ├── sqlite_project_repository.py   # implements ProjectRepository
│   │       │           └── sqlite_task_repository.py      # implements TaskRepository
│   │       │
│   │       └── adapters/
│   │           ├── rest/
│   │           │   ├── main.py         # FastAPI instance, includes routers
│   │           │   ├── deps.py         # dependency injection (repos, use cases)
│   │           │   ├── schemas.py      # Pydantic DTOs (request/response)
│   │           │   └── routers/
│   │           │       ├── projects.py
│   │           │       └── tasks.py
│   │           └── mcp/
│   │               ├── server.py       # MCP server (stdio)
│   │               └── tools.py        # defines tools, calling the same use cases
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
  infrastructure, the REST adapter, and the MCP adapter — under
  `backend/src/lifeos/domain/`, `application/`, `infrastructure/`,
  `adapters/rest/`, and `adapters/mcp/` respectively, each with its own test
  suite under `backend/tests/`. The application layer covers the full
  Projects/Tasks lifecycle (Step 9), including soft deletion and filtered
  listings; REST and MCP still expose only the original six operations.
- **Pending:** Phase 1 Step 8 (MVP closing) and Steps 10-13, which build the
  CLI and TUI adapters of
  [docs/adr/0008-keyboard-driven-tui-adapter.md](docs/adr/0008-keyboard-driven-tui-adapter.md)
  — see [docs/roadmap.md](docs/roadmap.md).

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

## Where the data lives

Every entry point (REST, MCP, and the planned CLI/TUI) is a separate
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
There is still no cross-process invalidation — a long-lived client must reload
rather than assume its view is authoritative.

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
