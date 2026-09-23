# Life OS

Life OS is a personal operating system that centralizes notes, passwords,
calendar, projects/tasks, and home inventory, with access and modification
through AI agents via a custom MCP (Model Context Protocol) server. It is
designed for a single, self-hosted user: an AI agent becomes a first-class
client of the system, using the same business rules as the web frontend,
CLI, or mobile app — never a workaround that talks to files or screenshots.

## Status

**Phase 1 (MVP: Projects + Tasks) is in progress.** The domain layer,
application use cases, SQLite infrastructure, REST adapter, MCP adapter, and
CLI adapter are implemented and merged — a full REST API, MCP server, and
`lifeos` command-line tool for Projects and Tasks are all available (see
[docs/mcp-setup.md](docs/mcp-setup.md) to connect an agent, or
[docs/cli.md](docs/cli.md) for the CLI). The TUI (Steps 12-13) and Step 8
(loading the roadmap into the app itself via an agent) remain to reach the
Phase 1 Definition of Done.

See [docs/roadmap.md](docs/roadmap.md) for the full phase breakdown and
current status of each step.

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + Pydantic v2 |
| ORM / DB | SQLModel + SQLite (MVP) → PostgreSQL (multi-device) |
| MCP Server | Official Python `mcp` SDK (stdio → HTTP/SSE) |
| Frontend | React + Vite + TypeScript, TailwindCSS |
| CLI/TUI | `Typer` + `Textual` |
| Android | Kotlin + Jetpack Compose, Retrofit |
| Containers | Docker + docker-compose |

Full rationale in [docs/adr/0006-tech-stack.md](docs/adr/0006-tech-stack.md).

## Architecture

Monorepo with hexagonal architecture: the domain layer does not depend on
FastAPI, SQLite, or MCP, and REST/MCP are two separate entry-point adapters
that execute the same use cases, so business rules apply consistently
regardless of which client originated the action. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the full layer breakdown.

## Roadmap

- [ ] **Phase 0** — Foundations (repo, Docker Compose, base data model, basic CI) — *in progress*
- [ ] **Phase 1** — MVP: Projects + Tasks (REST + minimal frontend + CLI/TUI + MCP server) — *in progress*
- [ ] **Phase 2** — Notes + cross-module search
- [ ] **Phase 3** — Calendar + reminders
- [ ] **Phase 4** — Home inventory
- [ ] **Phase 5** — Passwords / Vault
- [ ] **Phase 6** — Android app
- [ ] **Phase 7** — Hardening (rate limiting, auditing, backups, e2e tests)

Full detail per phase in [docs/roadmap.md](docs/roadmap.md), which is the
single source of truth for phasing and status.

## Documentation

- **Vision** — [docs/vision.md](docs/vision.md)
- **Roadmap** — [docs/roadmap.md](docs/roadmap.md)
- **Architecture** — [ARCHITECTURE.md](ARCHITECTURE.md)
- **Decisions (ADRs)** — [docs/adr/README.md](docs/adr/README.md)
- **Connecting an AI agent to the MCP server** — [docs/mcp-setup.md](docs/mcp-setup.md)
- **CLI reference** — [docs/cli.md](docs/cli.md)
- **Contributing** — [CONTRIBUTING.md](CONTRIBUTING.md)

## How to run / verify

- **Tests:** run `pytest` from `backend/` (domain and use-case tests run
  without a database, using in-memory fake repositories).
- **Local environment:** run `uv sync --all-extras` from `backend/` — it
  creates `.venv` and installs the exact versions pinned in
  `backend/uv.lock`, the same ones CI uses. Then run
  `uv run uvicorn lifeos.adapters.rest.main:app` for the REST API,
  `uv run lifeos-mcp` for the MCP server, or `uv run lifeos --help` for the
  CLI (see [docs/cli.md](docs/cli.md)). All three use the shared database
  described in [ARCHITECTURE.md](ARCHITECTURE.md#where-the-data-lives).
- **Updating dependencies:** change the version range in
  `backend/pyproject.toml`, then run `uv lock` and commit the updated
  `uv.lock`. CI installs with `--locked`, so it fails if the lock and the
  manifest disagree.
- **Docker Compose** (`docker compose up`, after copying `.env.example` to
  `.env`) still works, but is no longer the target way to run Life OS — it
  is being built as a local desktop app instead (a Quickshell client over a
  local REST daemon), see
  [docs/adr/0009-quickshell-desktop-client.md](docs/adr/0009-quickshell-desktop-client.md).
