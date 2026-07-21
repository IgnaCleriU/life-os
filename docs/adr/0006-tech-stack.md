# 0006. Technology stack

- Status: Accepted
- Date: 2026-07

## Context

Life OS spans several components (backend, MCP server, web frontend,
CLI/TUI, Android app) and needs a stack that: keeps the domain layer
framework-free (see [0001-hexagonal-monorepo.md](0001-hexagonal-monorepo.md)),
is well-supported for a solo developer to maintain, and integrates cleanly
with the MCP protocol for AI-agent access.

## Decision

Adopt the following stack:

| Layer | Choice | Alternatives considered |
|---|---|---|
| Backend | FastAPI + Pydantic v2 | — |
| ORM / DB | SQLModel or SQLAlchemy 2.0 (see [0003-sqlite-for-mvp-postgres-later.md](0003-sqlite-for-mvp-postgres-later.md) for engine choice) | — |
| Migrations | Alembic (introduced once schema stabilizes, see ADR 0003) | — |
| Auth | JWT (access + refresh tokens) with OAuth2 password flow | Passkeys/WebAuthn, considered for the future |
| MCP server | Official Python `mcp` SDK (stdio transport initially, HTTP/SSE later for remote access) | — |
| Frontend | React + Vite + TypeScript, TailwindCSS | SvelteKit |
| CLI/TUI | `Typer` (CLI) + `Textual` (TUI) | Click + Rich |
| Android | Kotlin + Jetpack Compose, Retrofit to consume the REST API | React Native (would share more code with the web frontend, but splits the mobile stack from native Android idioms) |
| Containers | Docker + Docker Compose for local development | — |
| Background jobs | APScheduler or Celery + Redis (reminders, notifications) | — |

Rationale highlights:
- **FastAPI + Pydantic v2** gives typed request/response DTOs at the REST
  boundary and async support, while keeping the domain layer free of
  these dependencies per ADR 0001.
- **SQLModel/SQLAlchemy 2.0** are used only inside `infrastructure/`,
  behind the repository ports defined in `application/ports/`.
- **JWT with OAuth2 password flow** is simple to implement for a
  single-user system and works across deployment targets (ADR 0005)
  without requiring a browser-based passkey ceremony; revisit if
  multi-device UX friction becomes a problem.
- **Official MCP Python SDK** is used rather than a hand-rolled protocol
  implementation, to stay compatible with Claude Desktop/Claude Code and
  other MCP-speaking agents without maintenance burden.
- **Typer + Textual** were chosen over Click + Rich for a more modern,
  type-hint-driven CLI/TUI developer experience.
- **Kotlin + Compose + Retrofit** follows current native Android
  conventions; React Native was considered for code-sharing with the web
  frontend but was not chosen, to keep the Android app idiomatic and avoid
  a cross-platform abstraction layer this early.
- **APScheduler/Celery + Redis** cover scheduled/background work (e.g.,
  Calendar reminders in a later phase); APScheduler is the lighter-weight
  starting option, with Celery + Redis available if job volume or
  reliability needs grow.

## Consequences

- The stack is consistent across the roadmap's phases (see
  [../roadmap.md](../roadmap.md)) — no component needs to be replaced to
  support Notes, Calendar, Inventory, or Passwords; only new modules and
  possibly new adapters are added.
- Domain purity (ADR 0001) constrains where each of these libraries may be
  imported: `fastapi`, `sqlmodel`/`sqlalchemy`, and `mcp` are confined to
  `adapters/` and `infrastructure/`.
- Choosing well-known, widely documented libraries (FastAPI, SQLAlchemy,
  React) reduces onboarding friction for both human contributors and AI
  coding agents working in this repo.
- Some alternatives (SvelteKit, Click+Rich, React Native, Passkeys) remain
  reasonable fallback choices and are recorded here so they are not
  re-litigated without cause; switching would warrant a new ADR.

## Alternatives considered

See the "Alternatives considered" column in the table above; each
alternative was judged reasonable but not chosen for the reasons stated in
the rationale section.
