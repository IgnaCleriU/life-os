# ⚠️ DEPRECATED — old Life OS codebase

> [!CAUTION]
> **Everything under `deprecated/` is old code with bad practices. Do not
> build on it, do not follow its rules, and do not treat its decisions as
> constraints.** Active development lives in [`new/`](../new/README.md).

## What this is

The first version of Life OS, frozen on 2026-10-24 and moved here as-is.
It was produced almost entirely by AI agents, without the owner
understanding the design. It is kept only so that patterns can be looked up.

## Why it is deprecated

- **The Java backend is a partial clone of the Python one.** `backend-java/`
  was built as a port that has to stay byte-compatible with `backend/`
  instead of as a design of its own. Most of its odd choices exist only to
  imitate Python: the storage format, the explicit column lists, the
  interop test, and the same JSON shape and error codes.
- **Two implementations share one database.** Every business rule lives
  twice, once per language, and only the storage format is checked between
  them, not the behaviour.
- **The decisions grew out of early design errors.** The ADRs in
  `docs/adr/` look reasonable one by one but start from wrong premises. They
  are **discarded**: none of them applies to `new/`.
- **The docs describe a system that no longer matches the code.**
  `ARCHITECTURE.md` and `CLAUDE.md` describe only Python, and ADR 0011 is
  still marked *Proposed* although its code was deployed.
- **Some architectural guarantees are only conventions.** In
  `backend-java/`, nothing in the build stops a controller from bypassing
  the use cases. A `test-jar` is published that nothing consumes.

## How to use it

- **Allowed:** read the Python code (`backend/`) to see how a pattern was
  applied, such as ports and adapters, in-memory fake repositories, or soft
  delete, and then decide in `new/` whether that pattern is worth having.
- **Not allowed:** copying code, copying a decision because an ADR says so,
  following the rules in `deprecated/CLAUDE.md` or `deprecated/AGENTS.md`, or
  keeping compatibility with anything here.

## What no longer works after the move

The move to `deprecated/` intentionally broke the following:

- **The `life-os` MCP server.** It is registered at
  `backend/.venv/bin/lifeos-mcp`, a path that no longer exists, so it fails
  to start.
- **CI.** The old workflow is now `deprecated/.github/workflows/ci.yml`, a
  location GitHub does not run.
- **The VPS update procedure.** `git pull && docker compose up` from the
  repository root no longer finds `docker-compose.yml`.
- **Every script, Dockerfile and doc path relative to the repository root.**

## Data

The existing databases (`~/.local/share/life-os/lifeos.db` and the one on the
VPS) hold mock data. `new/` owes them no compatibility and no migration.
