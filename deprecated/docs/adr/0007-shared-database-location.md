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

# 0007. One shared database in the user data directory

- Status: Accepted
- Date: 2026-07

## Context

Life OS has several entry points into the same data — the REST API, the MCP
server, and (planned) a CLI/TUI, see
[0006-tech-stack.md](0006-tech-stack.md). They are **separate operating
system processes**, started independently and from different working
directories: the REST API from wherever the backend is launched, and the
MCP server from wherever the MCP client happens to spawn it (its stdio
transport means the client owns the subprocess, see
[0002-mcp-consumes-use-cases.md](0002-mcp-consumes-use-cases.md)).

The default `DATABASE_URL` was `sqlite:///./lifeos.db` — a path relative to
the current working directory. Every process therefore resolved it against
its own cwd and silently created a *different* database. This was not
theoretical: four `lifeos.db` files accumulated in practice (two inside git
worktrees, one in a Docker volume, one at the repo root), with real data
split across two of them. Because SQLite creates a missing file rather than
failing, nothing surfaced the divergence — a client would simply appear to
have "lost" the data another client had written.

A related hazard: the MCP server had been registered pointing at a path
inside `.claude/worktrees/`. Worktrees are disposable, so removing one
would have deleted the database with it.

The requirement that ties this together is that the agent's view and the
user's view must be the same data. An agent that reads a different database
than the frontend is worse than no agent at all.

## Decision

Default the database to the user's data directory following the XDG Base
Directory spec: `$XDG_DATA_HOME/life-os/lifeos.db`, falling back to
`~/.local/share/life-os/lifeos.db` when `XDG_DATA_HOME` is unset.

Two properties matter more than the specific path:

- **Absolute, not cwd-relative.** All entry points converge on the same
  file regardless of where they are launched from, with no configuration.
- **Outside the repository.** Data is not tied to a checkout, a branch, or
  a worktree, and survives `git clean`.

`DATABASE_URL` continues to override the default, so pointing a process at
a different database (tests, Docker, a scratch copy) stays a one-variable
change. The application also creates the parent directory during bootstrap,
since SQLite will not create it and a fresh machine would otherwise fail to
open the file.

This decision concerns *where* the database file lives. The engine choice
(SQLite now, PostgreSQL later) is
[0003-sqlite-for-mvp-postgres-later.md](0003-sqlite-for-mvp-postgres-later.md)
and is unaffected.

## Consequences

- The REST API, the MCP server and the future TUI share one database with
  no setup, which is what makes the agent a first-class client of the same
  system rather than a parallel one (see [../vision.md](../vision.md)).
- The location is the conventional one for a Linux desktop application,
  so bundling the backend and TUI into a desktop app needs no path rework.
- Registering an entry point from a temporary directory no longer risks the
  data, because the data no longer lives next to the code.
- The database is now durable user data rather than a disposable artifact
  of a checkout. That strengthens the trigger condition in ADR 0003 for
  introducing Alembic: dropping and recreating the file on schema changes
  is no longer a harmless development habit.
- Containerized runs need `DATABASE_URL` set explicitly, since a container
  has its own filesystem and the host's data directory is only visible if
  mounted. This is an override rather than the default path.
- Backups now have a single, predictable target directory instead of
  needing to find scattered files.

## Alternatives considered

- **A path inside the repository (e.g. `backend/lifeos.db`), resolved
  absolutely:** fixes the cwd problem, but keeps user data inside a git
  checkout, where it is exposed to `git clean`, branch switching, and
  worktree removal — the failure mode observed above.
- **Requiring `DATABASE_URL` everywhere, with no default:** explicit and
  unambiguous, but pushes configuration into every client (including the
  MCP client's own config file) and fails closed on a fresh install for no
  benefit, since there is a sensible per-user default.
- **A Docker volume as the canonical store:** was the de facto situation
  for the REST API, but reachable only from inside a container, so the MCP
  server and a native TUI could not share it without routing every access
  through the container.
