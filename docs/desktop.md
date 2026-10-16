# Desktop client reference

Life OS runs on the desktop as two pieces
([adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md),
[specs/0002-quickshell-desktop-client.md](specs/0002-quickshell-desktop-client.md)):

- **`lifeos-daemon`**: the REST adapter as a `systemd --user` service,
  listening on `127.0.0.1` only.
- **The board** (`lifeos.board`): an overlay plugin for Omarchy's shell
  (Omarchy 4, which runs its desktop as one Quickshell process with
  plugins). It talks to the daemon. The MCP server, the `lifeos` CLI and
  `lifeos-tui` don't need the daemon; they open the shared database
  directly and keep working when it is down.

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
- links `desktop/omarchy-plugin` to `~/.config/omarchy/plugins/lifeos.board`;
- runs `systemctl --user enable --now lifeos-daemon`;
- rescans Omarchy's shell and runs `omarchy plugin enable lifeos.board`,
  which asks you to confirm in the terminal because it's third-party code.
  You can read the code first and enable it later.

Run it again after moving the checkout or recreating the venv. Because the
plugin is a link to this checkout, Omarchy reloads the board as soon as you
save a file in `desktop/omarchy-plugin/`.

Then bind a key in `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + SHIFT + T", "Life OS", "omarchy-shell shell toggle lifeos.board")
```

`SUPER + T` is already Omarchy's float toggle. Check yours with
`omarchy menu keybindings --print`. Built against Omarchy `4.0.0.alpha`,
plugin `schemaVersion: 1`.

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

## 3. The board

Three columns, **PROJECTS → TASKS → TASK**, a status bar, and the same
five modes and keymap as `lifeos-tui`. [tui.md](tui.md) is the reference
for every key, quick-add, and undo; `?` shows them on the board too, from
the same registry. Beyond the TUI:

- **Mouse:**
  - click selects;
  - click the `·`/`◐`/`✓` glyph to cycle the status;
  - Ctrl+click adds a task to the bulk selection;
  - double-click drills right;
  - drag a task (or the selection) onto a project to move it;
  - the detail pane's status, priority, due date and project are buttons;
  - `+` in the pane headers adds.
- **Quick-add preview:** while you type, the prompt asks the daemon how
  it reads the text and shows chips for title, `#project`, `!priority`
  and `@due`. `Enter` is refused while `#project` is unknown or
  ambiguous.
- **Inline description:** `E` (or a click) edits the description in the
  detail pane. `Esc` saves it, and `u` undoes it.
- **Live updates:**
  - The board polls `GET /revision`: every second while it's shown, every
    five while it's hidden.
  - Changes from the agent over MCP, the CLI or the TUI appear on their own.
  - New tasks pulse and show a toast; while the board is hidden they come
    as a desktop notification, and clicking it opens the board.
- **Hidden, not quit:** `q` or `Esc` from PROJECTS hides the overlay. The
  plugin stays loaded, so selection, filters and undo history are there
  next time.
- **Daemon down:** the status bar turns red with
  `daemon unreachable · systemctl --user status lifeos-daemon`. The last
  data stays visible but dimmed, and the board reconnects on its own when
  the daemon is back (with its new token).
- **Theme:** colors, font and corner radius come from the active Omarchy
  theme and switch with it.

## 4. Testing the board

- `node --test desktop/tests/*.test.mjs` tests the keymap, key sequences,
  undo stack and formatting (`desktop/omarchy-plugin/lib/`), including
  parity with the TUI's keymap (`desktop/tests/tui-keymap.json`, kept
  current by `backend/tests/adapters/tui/test_keymap_export.py`). CI runs
  it.
- `desktop/tests/qml/run_board.py` is a headless end-to-end check. It
  starts `lifeos-daemon` on a throwaway database, mounts `BoardView.qml`
  offscreen with minimal Quickshell/Omarchy stubs, and drives it with
  keys and the mouse, saving screenshots. It needs PySide6 and the
  system's EGL/GL libraries, so it isn't in CI:

  ```bash
  cd backend && uv run --with PySide6-Essentials python ../desktop/tests/qml/run_board.py --out /tmp/board-shots
  ```

- On the real desktop: `omarchy-shell shell toggle lifeos.board`. After
  editing QML, Omarchy hot-reloads installed plugins; for a stuck state
  use `omarchy-restart-shell`.
