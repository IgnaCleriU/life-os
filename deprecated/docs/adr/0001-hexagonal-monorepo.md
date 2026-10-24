> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../../../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](../../DEPRECATED.md).

# 0001. Monorepo with hexagonal architecture

- Status: Accepted
- Date: 2026-07

## Context

Life OS exposes the same business logic through at least two entry points:
a REST API (consumed by the web frontend, CLI/TUI, and the Android app) and
an MCP server (consumed by AI agents). Both entry points must execute
exactly the same use cases and enforce the same business rules — there is
no acceptable path where an AI agent, acting through MCP, bypasses
validation or auditing that the REST API enforces.

The project is single-user and starts with a single module (Projects +
Tasks), but the roadmap adds several more domain modules (Notes, Calendar,
Passwords, Home inventory) and more entry points (Android app talking
directly to the API) over time. The codebase needs a structure that keeps
these additions cheap without rewriting the core.

## Decision

Organize the backend as a single repository (monorepo) using hexagonal
architecture (ports and adapters). The domain layer (`domain/`) is pure
Python — it does not import `fastapi`, `sqlmodel`, or `mcp`. Dependencies
point inward only:

```
adapters (REST, MCP) ──► application (use cases) ──► domain (entities)
                                    ▲
infrastructure (DB) ────────────────┘ (implements the ports application defines)
```

See [../../ARCHITECTURE.md](../../ARCHITECTURE.md) for the full layer
breakdown and current state.

## Consequences

- Adding a new domain module (Notes, Calendar, ...) does not require
  touching existing domain code or use cases of other modules.
- Swapping the DB engine (SQLite → PostgreSQL) or adding a new adapter
  (e.g., Android talking directly to the API) means adding a new
  implementation of an existing port — the domain and use cases stay
  untouched.
- Domain and use-case tests run without a database, using in-memory fake
  repositories, which keeps the test suite fast.
- Requires discipline: contributors must resist the temptation to put
  business logic in adapters (REST routers, MCP tools) "just this once."
  Code review should treat that as a defect.
- A monorepo means backend, frontend, CLI, and future Android code share
  one history and one set of conventions, simplifying coordinated changes
  across the stack (at the cost of a larger single repository).

## Alternatives considered

- **Layered (MVC-style) architecture without explicit ports:** simpler to
  start, but the REST and MCP entry points would likely diverge in
  behavior over time as shortcuts accumulate in each adapter.
- **Multi-repo (separate repos per component):** avoids one large repo,
  but adds coordination overhead for a single-developer project at this
  stage; revisit if the team grows.
