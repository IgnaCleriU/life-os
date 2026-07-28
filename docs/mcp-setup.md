# Connecting an AI agent to the MCP server

The MCP server exposes the same Project/Task use cases as the REST API
(see [../ARCHITECTURE.md](../ARCHITECTURE.md) and
[adr/0002-mcp-consumes-use-cases.md](adr/0002-mcp-consumes-use-cases.md))
over the stdio transport, so a Claude Desktop/Code MCP client can spawn it
directly as a subprocess — no network exposure or Docker changes needed for
local development.

## 1. Install the backend package

From `backend/`, in a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This registers the `lifeos-mcp` console script (see `[project.scripts]` in
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

The server reads `backend/.env` (or the process environment) for
`database_url` the same way the REST adapter does (see
`infrastructure/config.py`); by default it uses `sqlite:///./lifeos.db`
relative to the working directory the client launches it from — set
`database_url` explicitly (or run the client with `cwd` set to `backend/`)
if you want it to share the same file as a locally running REST server.

## 3. Verify

Start a conversation with Claude and ask it to create a project and a task
under it using the `create_project`/`create_task` tools. Confirm the data
also shows up via `GET /projects` and `GET /projects/{id}/tasks` on the
REST API, pointed at the same database file.
