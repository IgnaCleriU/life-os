# CLAUDE.md

Guide for AI agents (e.g. Claude Code) working on this repo. Read it before starting.

**Life OS** is a personal operating system (notes, passwords, calendar,
projects/tasks, home inventory) accessible by AI agents through a custom
MCP server.
**Current status:** Phase 1 MVP of **Projects + Tasks** — domain, ports,
use cases, SQLite infrastructure, the REST (as `lifeos-daemon`), MCP, CLI,
and TUI adapters, and the Omarchy board (`desktop/omarchy-plugin/`,
[ADR 0009](docs/adr/0009-quickshell-desktop-client.md)) are implemented.
Next is closing the MVP (Step 8); see [docs/roadmap.md](docs/roadmap.md)
for details.

## Mandatory documentation

Before designing or implementing, review these documents:

- [ARCHITECTURE.md](ARCHITECTURE.md) — hexagonal architecture and dependency rule (current state).
- [docs/vision.md](docs/vision.md) — product vision and rationale.
- [docs/roadmap.md](docs/roadmap.md) — phased roadmap, single source of truth for phasing and status.
- [docs/agentic-workflow.md](docs/agentic-workflow.md) — how to organize work (orchestrator + subagents).
- [CONTRIBUTING.md](CONTRIBUTING.md) — commit convention, atomic commits, and PR flow.
- [docs/adr/README.md](docs/adr/README.md) — Architecture Decision Records
  index. ADRs stay short (~1 page): the decision and why, not the design.
- [docs/specs/README.md](docs/specs/README.md) — paired design/implementation
  docs for ADRs that need more than a page (UI, data flow, task breakdown).

## Hard rules

- **No new code until the user understands it.** The user is reviewing
  `backend-java/` with Claude as a tutor
  ([docs/backend-java/README.md](docs/backend-java/README.md)). Until the
  user declares that review finished, Claude writes **no code at all**
  (production or tests, in any language): it reads, explains, and writes
  the study material under `docs/backend-java/`. After the review, any
  code change is explained first, and Claude writes it only once the user
  confirms they understand what it does and why. This rule overrides the
  "implement" steps of the agentic workflow below.
- **Commits are made by the user, never by Claude.** Claude does not run
  `git commit` (nor amend, rebase or push on the user's behalf). It leaves
  the changes in the working tree and proposes the Conventional Commit
  message(s); the user reviews and commits.
- **Hexagonal architecture:** the domain (`domain/`) is pure Python and
  **does not import** `fastapi`, `sqlmodel`, or `mcp`. Dependencies point
  inward (`adapters → application → domain`). Detail in
  [ARCHITECTURE.md](ARCHITECTURE.md).
- **MCP never accesses the DB directly:** it consumes the same use cases as
  the REST adapter.
- **Never delete or reset the local database**
  (`~/.local/share/life-os/lifeos.db`) without explicit confirmation from
  the user. It holds real personal data, not scratch/test data. The
  "delete it and let the app recreate it" remedy mentioned in
  [docs/roadmap.md](docs/roadmap.md) and [docs/tui.md](docs/tui.md) for
  schema changes is destructive — it erases every project and task
  currently stored. Confirm with the user first (and suggest a backup)
  rather than running it as a routine fix.
- **Agentic workflow:** understand → investigate (subagents in parallel) →
  plan (except for very small tasks) → implement (in parallel or in series
  depending on dependencies) → integrate and verify. See
  [docs/agentic-workflow.md](docs/agentic-workflow.md).
- **Parallel agents:** run each agent in its own **git worktree** (the
  worktree option in Claude Code) so their branches don't collide. See
  [docs/agentic-workflow.md](docs/agentic-workflow.md#5-parallel-agents-isolation-with-git-worktrees).
- **Commits:** [Conventional Commits](CONTRIBUTING.md#commit-convention)
  and **atomic** (several commits per task, one per logical change),
  made by the user (see above).
- **PRs:** never commit directly to `master`; work on a branch
  `<type>/<short-description>` and open a PR against `master`. The branch name
  must reflect the task — do **not** keep the auto-generated `claude/...`
  name. See [CONTRIBUTING.md](CONTRIBUTING.md#pull-request-flow).

## How to run / verify

- **Tests:** run `uv run pytest` from `backend/` (domain and use-case tests
  run without a database, using in-memory fake repositories), and
  `node --test desktop/tests/*.test.mjs` for the board's JS libraries. The
  board's QML has a headless harness, see
  [docs/desktop.md](docs/desktop.md#4-testing-the-board).
- **Commit validation:** `pre-commit install --hook-type commit-msg` (once
  per clone); validates the message format before a commit is created.
- **Local environment:** `uv sync --all-extras` from `backend/` creates
  `.venv` from the pinned versions in `backend/uv.lock`, then
  `uv run lifeos-daemon` (REST, token-guarded, see
  [docs/desktop.md](docs/desktop.md)) or `uv run lifeos-mcp` (MCP). Both
  share one database, see
  [ARCHITECTURE.md](ARCHITECTURE.md#where-the-data-lives).
- **Dependencies are locked.** Never add a bare, unconstrained requirement:
  every entry in `backend/pyproject.toml` carries a version range with an
  upper bound, and `backend/uv.lock` is committed. After touching the
  manifest run `uv lock` and commit the result — CI installs with
  `uv sync --locked` and fails if the two disagree.
- **Docker Compose** still works but is no longer the target runtime; Life
  OS is being built as a local desktop app (a Quickshell client over a
  local REST daemon, see
  [docs/adr/0009-quickshell-desktop-client.md](docs/adr/0009-quickshell-desktop-client.md)).
  [docs/adr/0005-deployment-target.md](docs/adr/0005-deployment-target.md)
  is superseded — do not treat it as current.
- **VPS deployment** is an optional second target (ADR 0010, 0013): Docker
  Compose with the Java API bound to loopback and its own database. It is
  reached over SSH, and publicly over HTTPS only through Caddy on 443 (the
  opt-in `public` profile). Files live in `deploy/` and the procedure in
  [docs/deployment.md](docs/deployment.md). Never publish port 8000
  directly, and never set `LIFEOS_API_AUTH=disabled` on a VPS: with public
  HTTPS the token is the only barrier. After any deploy change, run the
  post-deploy check in that guide.
