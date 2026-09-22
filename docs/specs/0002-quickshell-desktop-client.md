# 0002. Quickshell desktop client

- ADR: [adr/0009-quickshell-desktop-client.md](../adr/0009-quickshell-desktop-client.md)

## Problem

ADR 0009 makes a Quickshell overlay the primary human interface. It talks
to the use cases over REST, served by a local daemon. Three things are
missing today:

- **The REST adapter is not ready to be a daily product surface.** It has
  no auth, so any local process or a web page in the browser can call it.
  It has no way to tell a client that the data changed. And it has no
  quick-add: that parser and the `#project` resolution live only in the
  CLI and TUI adapters.
- **There is no daemon.** The API only runs when someone starts `uvicorn`
  by hand, and nothing tells a client which port or credentials to use.
- **There is no client.** The approved browser prototype shows the target
  behaviour: the TUI's panes, modes and keymap, plus mouse, blur, live
  quick-add preview, notifications and live updates. None of it exists as
  QML.

### Scope

In scope: the full Projects/Tasks board as an overlay, reaching feature
parity with `lifeos-tui` as documented in [../tui.md](../tui.md), plus the
backend work it needs.

Out of scope, and left for their own specs: the bar widget, the
standalone quick-capture popup, Notes and the other modules, remote or
multi-device access, and distro packaging.

## Design

### Processes

```
Hyprland ── bind SUPER+T ──► qs -c lifeos ipc call board toggle
                                   │
                    Quickshell (qs -c lifeos)            MCP client (Claude)
                    overlay: PROJECTS · TASKS · TASK          │ stdio
                                   │ HTTP 127.0.0.1           ▼
                                   ▼                      lifeos-mcp
              lifeos-daemon (systemd --user) = REST adapter    │
                                   │                          │
                                   └──► use cases ◄───────────┘   (+ lifeos CLI, lifeos-tui)
                                             │
                                  ~/.local/share/life-os/lifeos.db  (ADR 0007, WAL)
```

The daemon is the existing FastAPI app. It adds no new layer: the daemon
is only a process and a launcher. MCP, CLI and TUI keep opening the
database in process. They don't depend on the daemon, and they still
work when it's down.

### Daemon

A new console script, `lifeos-daemon`, in the REST adapter:

1. Generates a random token (32 bytes, url-safe) at every start.
2. Writes `$XDG_RUNTIME_DIR/life-os/daemon.json` with the `port` and the
   `token`, in a directory with mode `0700` and a file with mode `0600`.
   The runtime dir is a tmpfs that only this user can read, and it is
   wiped on logout, so the token never outlives the session.
3. Runs uvicorn on `127.0.0.1` only, on a port from settings (default
   `8000`, as today).

It ships as a user unit, `desktop/systemd/lifeos-daemon.service`, with
`Restart=on-failure` and `WantedBy=default.target`.

### Auth

- Every route except `GET /health` requires the header
  `Authorization: Bearer <token>`. Otherwise it returns `401` with the
  usual structured error body (`unauthorized`).
- Requests whose `Host` header is not `127.0.0.1:<port>` or
  `localhost:<port>` are rejected with `403`, to block DNS rebinding.
- The app sends no CORS headers. The custom `Authorization` header forces
  a browser preflight, the preflight fails, and so a web page can neither
  read nor write.
- Auth is on by default. Tests and ad-hoc `uvicorn` runs turn it off
  explicitly with `LIFEOS_API_AUTH=disabled`. There is no silent
  unauthenticated mode.

### REST additions

| Route | Purpose |
|---|---|
| `GET /revision` | Returns `{"revision": "<opaque>"}`. The value changes after any commit by any process. |
| `POST /quick-add/preview` | Body `{text, default_project_id?}`. Returns the parsed `title`, `priority`, `due_date` and the resolved `project` (`{id, name}` or `null`), plus `error` (`{code, message}` or `null`). It never writes. |
| `POST /quick-add` | Same body. Creates the task and returns `201` with a `TaskResponse`. On error it uses the same codes as the preview (`project_not_found`, `ambiguous_project_name`, `validation_error`). |

**Revision.** A new port, `RevisionSource.current() -> str`, reached
through a `GetRevision` use case. The SQLite implementation keeps one
dedicated read-only connection and returns `PRAGMA data_version` from it.
That value changes whenever *another* connection commits, whether in this
process or another one. The daemon's own writes go through its pool, not
through that connection, so every write is covered and no schema change
is needed. The value is opaque: clients only compare it for equality, and
a daemon restart simply triggers one extra refetch.

**Quick-add.** The tokenizer (`adapters/shared/quick_add.py`) is already
shared. Deciding which project a task lands in is not: today the CLI and
the TUI module each do it their own way. That logic moves to
`adapters/shared/capture_target.py`:

1. An explicit `#name` wins.
2. Otherwise `default_project_id`.
3. Otherwise the CLI's get-or-create "inbox" project.

An ambiguous or unknown `#name` is an error, never a guess. The CLI, the
TUI module and the REST routes all call it, so the three can't drift.

### Client layout

```
desktop/
├── quickshell/lifeos/            # symlinked to ~/.config/quickshell/lifeos
│   ├── shell.qml                 # ShellRoot, IpcHandler "board" (toggle/show/hide)
│   ├── Board.qml                 # PanelWindow on WlrLayer.Overlay, exclusive keyboard focus while shown
│   ├── panes/                    # ProjectsPane, TasksPane, DetailPane
│   ├── modals/                   # Prompt, Picker, Confirm, Palette, Help
│   ├── StatusBar.qml  Toasts.qml
│   ├── services/                 # Api (XHR + token), Sync (revision polling), Theme
│   ├── lib/                      # .pragma library JS, no Qt imports
│   │   ├── keymap.js  dispatch.js  undo.js  format.js
│   └── tests/                    # node harness for lib/ (strips the pragma, runs in vm)
└── systemd/lifeos-daemon.service
```

`services/Api` reads `daemon.json` at startup and again after any `401`
or connection error, because the token rotates when the daemon restarts.

### User interface

The browser prototype approved with ADR 0009 is the visual reference:

- One translucent, blurred layer-shell overlay, centered, with the three
  Miller columns PROJECTS · TASKS · TASK and a status bar.
- Row glyphs `·` `◐` `✓`, the same as the TUI.
- Priority and due-date markers, with overdue shown in the theme's red.
- A done/total progress bar per project.

`SUPER+T` toggles the overlay through IPC. `q`, or `Esc` from the leftmost
pane, *hides* the overlay without quitting, so the next toggle is instant
and state such as the selection, filters and undo history survives.

**Modes, keymap, quick-add, destructive actions:** identical to
[0001](0001-keyboard-driven-tui-adapter.md#keymap) and
[../tui.md](../tui.md). That keymap table stays the single source of
truth. The JS registry (`lib/keymap.js`) drives dispatch, the palette
and the `?` overlay, as the TUI's registry does. Two tests guard it:

- a test that no binding is a strict prefix of another;
- a parity test against `desktop/quickshell/lifeos/tests/keymap.json`,
  a fixture that a Python test exports from the TUI registry and keeps
  current.

Two keys behave differently: `E` edits the description inline in the
detail pane instead of suspending the board for `$EDITOR`, and `y` copies
through `wl-copy`.

**Mouse, which the TUI lacks:**
- Click selects a row and focuses its pane.
- Click on a glyph cycles the status.
- Double-click drills right.
- Ctrl+click toggles bulk selection.
- Dragging a task, or the whole bulk selection, onto a project moves it.
- Status, priority, due date and project in the detail pane are clickable
  controls.
- Pane headers have a `+` button.

**Quick-add preview:** the prompt calls `POST /quick-add/preview`,
debounced by about 120 ms, and shows the result as chips for title,
`#project`, `!priority` and `@due`, with errors inline. `Enter` is
refused while there is an error.

**Undo:** same semantics as the TUI, kept per session on the client. Before
each write, the client captures the prior value and undoes with the
inverse REST call: the `restore` routes for deletes, `PATCH` for field
edits, the transition routes for status, and `move` for moves.

### Live updates and notifications

`services/Sync` polls `GET /revision`: every 1 s while the overlay is
shown, every 5 s while it's hidden. When the value changes it refetches
the projects and the current project's tasks, then diffs by id.

After its own writes the client records the new revision, so it never
notifies about its own changes. External changes, which in practice come
from the agent over MCP or from the CLI, show up as:

- rows that pulse briefly while the overlay is visible;
- a desktop notification via `notify-send` (mako on Omarchy) while it's
  hidden, e.g. "2 tasks added to Casa".

The source of a change can't be named yet (see Open questions).

### Daemon down

If a request fails to connect, or `daemon.json` is missing:

- The status bar shows a red `daemon unreachable`, together with the hint
  `systemctl --user status lifeos-daemon`.
- Writes are disabled and the last loaded data stays visible, dimmed.
- Sync retries with backoff until the daemon answers.

### Theme

Colors come from the active Omarchy theme under
`~/.config/omarchy/current/theme/`. `services/Theme` watches it with a
`FileView` and falls back to a built-in Tokyo Night palette. Only
semantic roles are used: background, foreground, dim, accent, secondary
accent, green, yellow and red.

### Hyprland bindings

```
exec-once = qs -c lifeos
bind = SUPER, T, exec, qs -c lifeos ipc call board toggle
bind = SUPER SHIFT, T, exec, omarchy-launch-or-focus-tui "lifeos-tui" lifeos-tui
```

These replace the `SUPER, T` example in [../tui.md](../tui.md): the TUI
moves to `SUPER SHIFT, T`. Check both against the local Omarchy binds
before using them.

## Implementation tasks

| # | Task | Notes |
|---|---|---|
| 1 | Token auth + `Host` check in the REST adapter; `LIFEOS_API_AUTH=disabled` for tests | Update the REST test fixtures. Test `401`, `403`, and that `/health` stays open. |
| 2 | `lifeos-daemon` console script: token + `daemon.json` + loopback-only uvicorn | Test the file permissions and the content of `daemon.json`. |
| 3 | `RevisionSource` port, `GetRevision` use case, SQLite `data_version` implementation, `GET /revision` | Test that a write from a *separate* connection changes the revision. |
| 4 | `adapters/shared/capture_target.py`; CLI `capture` and the TUI module switched to it | Pure refactor: the existing CLI and TUI tests must pass unchanged. |
| 5 | `POST /quick-add/preview`, `POST /quick-add` | Reuses tasks 4 and the shared parser. |
| 6 | `desktop/systemd/lifeos-daemon.service`, `desktop/install.sh` (links the QML config and the unit), `docs/desktop.md` | No distro package. |
| 7 | QML skeleton: `shell.qml` + IPC toggle, overlay window, `Api`/`Sync` services, daemon-down state | Manual check on Omarchy. |
| 8 | `lib/` JS: keymap registry + dispatch, undo, formatting; node test harness; keymap fixture exported from the TUI and a parity test | These are the only automated tests on the QML side. |
| 9 | Panes, modes, modals (prompt with live preview, picker, confirm, palette, help), status bar | Keyboard parity with [../tui.md](../tui.md). |
| 10 | Mouse interactions, inline description editing, drag-to-move | |
| 11 | Live refresh diffing, pulses and toasts, `notify-send` while hidden | |
| 12 | Omarchy theme reader with fallback | |
| 13 | Docs: ARCHITECTURE (daemon, `desktop/`, the shared helper), tui.md binds, roadmap status | |

Tasks 1-5 are backend-only and land first; each is useful without the
client. Task 6 needs 1-2. Tasks 7-12 need 1-6. Task 8 has no Qt
dependency and can run in parallel with 7.

## Open questions

- **Which Omarchy theme file to parse.** The theme directory holds
  per-app files (terminal, Waybar, Hyprland), not one palette file. The
  choice needs checking on a real install. The fallback palette keeps
  this non-blocking.
- **Quickshell version.** Quickshell is pre-1.0 and its QML API still
  moves. Pin the version the client is built against in
  `docs/desktop.md`.
- **Change attribution.** Showing "added by Claude" needs a `source` or
  audit field, which is a schema change. It waits for Alembic
  ([0003](../adr/0003-sqlite-for-mvp-postgres-later.md)) and Phase 7
  audit logging.
- **Server-sent events** instead of polling, once streaming in QML's JS
  engine is verified. `GET /revision` stays either way.
- **TUI parity for future modules.** Whether Notes and later modules get
  TUI screens or stay Quickshell-only. It is decided per module, not here.
