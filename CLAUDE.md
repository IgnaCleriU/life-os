# CLAUDE.md

Guide for AI agents (e.g. Claude Code) working on this repo. Read it before starting.

**Life OS** is a personal operating system (notes, passwords, calendar,
projects/tasks, home inventory) accessible by AI agents through a custom
MCP server.
**Current status:** Phase 0 / MVP of **Projects + Tasks** — the domain
layer is implemented, the rest is pending (see
[docs/roadmap.md](docs/roadmap.md) for details).

## Mandatory documentation

Before designing or implementing, review these documents:

- [ARCHITECTURE.md](ARCHITECTURE.md) — hexagonal architecture and dependency rule (current state).
- [docs/vision.md](docs/vision.md) — product vision and rationale.
- [docs/roadmap.md](docs/roadmap.md) — phased roadmap, single source of truth for phasing and status.
- [docs/agentic-workflow.md](docs/agentic-workflow.md) — how to organize work (orchestrator + subagents).
- [CONTRIBUTING.md](CONTRIBUTING.md) — commit convention, atomic commits, and PR flow.
- [docs/adr/README.md](docs/adr/README.md) — Architecture Decision Records index.

## Hard rules

- **Hexagonal architecture:** the domain (`domain/`) is pure Python and
  **does not import** `fastapi`, `sqlmodel`, or `mcp`. Dependencies point
  inward (`adapters → application → domain`). Detail in
  [ARCHITECTURE.md](ARCHITECTURE.md).
- **MCP never accesses the DB directly:** it consumes the same use cases as
  the REST adapter.
- **Agentic workflow:** understand → investigate (subagents in parallel) →
  plan (except for very small tasks) → implement (in parallel or in series
  depending on dependencies) → integrate and verify. See
  [docs/agentic-workflow.md](docs/agentic-workflow.md).
- **Parallel agents:** run each agent in its own **git worktree** (the
  worktree option in Claude Code) so their branches don't collide. See
  [docs/agentic-workflow.md](docs/agentic-workflow.md#5-parallel-agents-isolation-with-git-worktrees).
- **Commits:** [Conventional Commits](CONTRIBUTING.md#commit-convention)
  and **atomic** (several commits per task, one per logical change).
- **PRs:** never commit directly to `master`; work on a branch
  `<type>/<short-description>` and open a PR against `master`. The branch name
  must reflect the task — do **not** keep the auto-generated `claude/...`
  name. See [CONTRIBUTING.md](CONTRIBUTING.md#pull-request-flow).

## How to run / verify

- **Tests:** run `pytest` from `backend/` (domain and use-case tests run
  without a database, using in-memory fake repositories).
- **Commit validation:** `pre-commit install --hook-type commit-msg` (once
  per clone); validates the message format before a commit is created.
- **Local environment:** `docker compose up` starts the backend (see
  [ARCHITECTURE.md](ARCHITECTURE.md)).
