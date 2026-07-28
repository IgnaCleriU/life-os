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
│   │       │   └── use_cases/
│   │       │       ├── create_project.py
│   │       │       ├── list_projects.py
│   │       │       ├── create_task.py
│   │       │       ├── list_tasks.py
│   │       │       ├── update_task.py
│   │       │       └── complete_task.py
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
  suite under `backend/tests/`.
- **Pending:** Phase 1 Step 8 (MVP closing) — see
  [docs/roadmap.md](docs/roadmap.md).

See [docs/roadmap.md](docs/roadmap.md) for the phased plan.

## MCP server

The MCP server **does not access the database directly**: it consumes the
same use cases exposed by the REST adapter. This guarantees that business
rules (validation, permissions, auditing) are always applied, regardless of
whether the action originated from an AI agent, the frontend, or the CLI.

## Maintaining this document

Update it when:
- A new domain module is added (Notes, Calendar, Inventory, Passwords —
  Phase 2+).
- A new entry-point adapter is added (e.g. an Android app talking directly
  to the API).
- SQLite is replaced by PostgreSQL, or an existing port changes.

Significant architectural decisions should also be recorded as an ADR — see
[docs/adr/README.md](docs/adr/README.md).
