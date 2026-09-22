# Desktop client reference

Life OS runs on the desktop as two pieces
([adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md),
[specs/0002-quickshell-desktop-client.md](specs/0002-quickshell-desktop-client.md)):

- **`lifeos-daemon`**: the REST adapter as a `systemd --user` service,
  listening on `127.0.0.1` only.
- **The Quickshell board**: an overlay that talks to the daemon. The MCP
  server, the `lifeos` CLI and `lifeos-tui` don't need the daemon; they open
  the shared database directly and keep working when it is down.

## 1. Install

From the repository root, once `backend/.venv` exists (`uv sync --all-extras`
in `backend/`):

```bash
desktop/install.sh              # install the unit and link the Quickshell config, then start the daemon
desktop/install.sh --no-start   # install without touching systemctl
desktop/install.sh --uninstall  # remove the unit and the link (your data stays)
```

The script:
- writes `~/.config/systemd/user/lifeos-daemon.service`, pointing at this
  checkout's `backend/.venv/bin/lifeos-daemon`;
- links `desktop/quickshell/lifeos` to `~/.config/quickshell/lifeos`;
- runs `systemctl --user enable --now lifeos-daemon`.

Run it again after moving the checkout or recreating the venv.

## 2. The daemon

```bash
systemctl --user status lifeos-daemon
journalctl --user -u lifeos-daemon -f
```

On every start the daemon generates a new random token and writes
`$XDG_RUNTIME_DIR/life-os/daemon.json` with mode `0600`:

```json
{"base_url": "http://127.0.0.1:8000", "port": 8000, "token": "…", "pid": 1234}
```

Clients read this file to find the daemon and send
`Authorization: Bearer <token>` on every request. When the daemon stops, it
deletes the file. `APP_PORT` changes the port (default `8000`) and
`DATABASE_URL` changes the database, exactly as for every other entry point.

### Auth, briefly

- Every route except `GET /health` needs the bearer token. A request without
  it gets `401` with `unauthorized`.
- A request whose `Host` is not `localhost`, `127.0.0.1` or `::1` gets `403`
  with `forbidden_host`. This blocks DNS rebinding.
- No CORS headers are sent, so a web page in your browser can't use the API.

For a manual `uvicorn lifeos.adapters.rest.main:app` run (development,
Docker), set `LIFEOS_API_TOKEN` to a long random value. Alternatively,
`LIFEOS_API_AUTH=disabled` turns the guard off, but only use it with the
port bound to loopback. Auth is never off by default.

### Endpoints the board uses beyond CRUD

| Route | Purpose |
|---|---|
| `GET /revision` | `{"revision": "<opaque>"}`. It changes after any commit by any process: the daemon, MCP, the CLI or the TUI. Poll it and refetch when it changes. |
| `POST /quick-add/preview` | `{text, default_project_id?}` returns how the text would be parsed (`title`, `priority`, `due_date`, `project`, `error`), without writing anything. `project.id` is `null` when the task would go to an `inbox` project that doesn't exist yet. |
| `POST /quick-add` | Same body. Creates the task and returns `201`. Returns `404 project_name_not_found` or `409 ambiguous_project_name` for a bad `#project`. |

Quick-add syntax and the `#project` rule are the same as the CLI's; see
[cli.md](cli.md#4-quick-add-syntax).
