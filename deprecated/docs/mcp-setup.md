> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](../DEPRECATED.md).

# Connecting an AI agent to the MCP server

The MCP server exposes the same Project/Task use cases as the REST API
(see [../ARCHITECTURE.md](../ARCHITECTURE.md) and
[adr/0002-mcp-consumes-use-cases.md](adr/0002-mcp-consumes-use-cases.md))
over the stdio transport, so a Claude Desktop/Code MCP client can spawn it
directly as a subprocess — no network exposure or Docker changes needed for
local development.

## 1. Install the backend package

From `backend/`:

```bash
uv sync --all-extras
```

This creates `.venv` with the exact versions pinned in `backend/uv.lock`, so
your MCP server runs the same dependency set as CI.

It also registers the `lifeos-mcp` console script (see `[project.scripts]` in
`backend/pyproject.toml`), which runs `lifeos.adapters.mcp.server:main` —
creates the SQLite tables if they don't exist yet, then serves the MCP
tools over stdio.

## 2. Point Claude Desktop/Code at it

Add an entry to Claude's MCP server configuration
(`claude_desktop_config.json` for Desktop, or the equivalent MCP settings
for Claude Code), pointing `command` at the `lifeos-mcp` binary inside the
venv you just created:

```json
{
  "mcpServers": {
    "life-os": {
      "command": "/absolute/path/to/life-os/backend/.venv/bin/lifeos-mcp"
    }
  }
}
```

With Claude Code the same thing can be done from the CLI, without editing
JSON by hand — `--scope user` makes it available in every project, not just
the one you happen to be in:

```bash
claude mcp add life-os --scope user -- /absolute/path/to/life-os/backend/.venv/bin/lifeos-mcp
```

Point `command` at a **stable checkout**, not at a `.claude/worktrees/...`
path: worktrees are temporary, and a server registered inside one stops
working (and takes its database with it) as soon as the worktree is
removed.

No `DATABASE_URL` is needed. By default the server uses the user data
directory — `$XDG_DATA_HOME/life-os/lifeos.db`, i.e.
`~/.local/share/life-os/lifeos.db` — which does not depend on the working
directory the MCP client happens to launch it from, so the REST API, the
MCP server, and the future TUI all share one database automatically. Set
`DATABASE_URL` only to deliberately point somewhere else.

## 3. Available tools

The server exposes the full Projects/Tasks lifecycle, each tool calling the
same use case as its REST equivalent (ADR 0002):

- **Projects:** `create_project`, `list_projects` (optional `status`, `text`
  filters), `get_project`, `update_project` (partial; `description: null`
  clears it), `complete_project`, `archive_project`, `activate_project`,
  `delete_project` (fails if the project still has live tasks),
  `restore_project`.
- **Tasks:** `create_task`, `list_tasks` (optional `project_id`, `status`,
  `due_before`, `text` filters — omit `project_id` to list across all
  projects), `get_task`, `update_task` (partial; `description: null` and
  `due_date: null` each clear that field), `complete_task`, `start_task`,
  `reopen_task`, `move_task`, `delete_task`, `restore_task`.

Deletion is soft: a deleted project or task disappears from every listing and
from `get_*`, but is not gone — only the session that deleted it (the TUI's
undo stack) can bring it back with `restore_project`/`restore_task`.

## 4. Verify

Start a conversation with Claude and ask it to create a project and a task
under it using the `create_project`/`create_task` tools. Confirm the data
also shows up via `GET /projects` and `GET /projects/{id}/tasks` on the
REST API, pointed at the same database file.
