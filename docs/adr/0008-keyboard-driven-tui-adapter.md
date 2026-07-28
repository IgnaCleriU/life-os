# 0008. Keyboard-driven TUI adapter

- Status: Accepted
- Date: 2026-07

## Context

Life OS currently has two entry points into the application layer: the REST
adapter and the MCP adapter (see
[0002-mcp-consumes-use-cases.md](0002-mcp-consumes-use-cases.md)). Neither is
usable as a day-to-day human interface: REST needs a client, and MCP requires
opening a conversation with an agent. Phase 1 of
[../roadmap.md](../roadmap.md) already calls for a "basic CLI/TUI", and
[0006-tech-stack.md](0006-tech-stack.md) selected Typer and Textual for it,
but neither document defines what that interface actually is.

The forces at play:

- **A native desktop application, not a hosted service.**
  [../vision.md](../vision.md) targets one self-hosted user, and
  [0005-deployment-target.md](0005-deployment-target.md) has been deprecated
  precisely because it framed deployment as a hosting question: Life OS is
  being built as a native TUI desktop application for Omarchy, launching the
  backend and the interface together on the user's own machine. There is no
  server to reach and no remote client to design around.
- **One database, at a known absolute path.**
  [0007-shared-database-location.md](0007-shared-database-location.md) places
  the SQLite file in the user's data directory, so every entry point converges
  on the same data with no configuration — the property that makes an
  in-process client show exactly what the agent sees.
- **Keyboard-first environment.** The target desktop is Omarchy (Hyprland),
  where system settings are manipulated entirely by keyboard through two
  distinct surfaces: a narrow fuzzy menu for one-shot commands
  (`omarchy-menu`, built on Walker in dmenu mode) and full-screen terminal
  UIs for stateful domains (Impala for Wi-Fi, bluetui for Bluetooth, launched
  through `omarchy-launch-or-focus-tui`). Both surfaces are generated from
  small composable commands that carry their own metadata, so the menu is a
  discoverable mirror of the commands rather than a parallel implementation.
- **A narrow existing use-case surface.** The application layer today exposes
  `CreateProject`, `ListProjects`, `CreateTask`, `ListTasks`, `UpdateTask` and
  `CompleteTask`. There is no delete, no project mutation, no lookup by id, no
  way to move a task between projects, no way to reach the `doing` state, and
  no way to list tasks outside a single project — even though the domain
  entities already implement most of those transitions.
- **A deliberate build order.** The application layer is completed first, and
  the TUI is built against it afterwards. A web frontend is explicitly
  deferred to a later step.

Only Projects and Tasks exist as a domain module. The later modules described
in [../vision.md](../vision.md) are out of scope here and are not designed by
this ADR.

## Decision

Add a keyboard-driven desktop client as a new adapter, `adapters/tui/`,
accompanied by a non-interactive `adapters/cli/` entry point. Both are
drivers of the application layer and, exactly as in ADR 0002, contain no
business logic of their own: they translate between keystrokes (or CLI
arguments) and use cases.

### Scope of this decision

This ADR covers the **client interface**: the board, its keymap, and how it
reaches the application layer, with both running on the user's machine against
the shared database of ADR 0007.

It deliberately does not settle the rest of the desktop-app question: how the
application is packaged and launched, the authentication decision that Phase 0
of [../roadmap.md](../roadmap.md) leaves open (JWT was chosen for a networked
backend, which a local desktop app is not), or remote and multi-device access
for the Android app in Phase 6. Those belong to the desktop-app ADR that
[0005-deployment-target.md](0005-deployment-target.md) is waiting to be
superseded by. This ADR narrows the interface question rather than answering
those in passing, so 0005 stays `Deprecated` and is not marked superseded by
this one.

Within that scope, the module surface is the Projects and Tasks entities **as
they exist today** — name, description, status, priority, due date. Tags and
subtasks, listed for this module in [../vision.md](../vision.md), are
deliberately not part of this step; they are deferred until the interface has
been in real use long enough to show whether they are missed.

### The TUI is the reference client

Because it is the only human interface, the TUI defines completeness for the
module: **every capability the system has for Projects and Tasks must be
reachable from it.** Anything not reachable from the TUI does not exist for
the user.

This runs in the useful direction. Each capability is added as a use case
first, so REST and MCP gain it at the same time and at no extra cost — which
is how the gaps listed below get closed for every adapter at once, not just
for the terminal.

### Access to the application layer

The TUI and CLI call use cases **in process**, wiring the SQLite repositories
through their own `deps.py`, the same way `adapters/rest/deps.py` and
`adapters/mcp/deps.py` do. They do not talk to the REST API over HTTP.

This follows from Life OS being a desktop application rather than a hosted
service: there is no server to reach, so requiring one to be running would be
a constraint the design imposes on itself. An in-process client starts
instantly, works with nothing else running, and adds no failure mode between a
keystroke and a write. Going through HTTP would not increase reuse — the reuse already lives at the
use-case layer, per ADR 0002 — it would only add a transport, an HTTP client,
DTO deserialization, and a mapping from status codes back to domain errors.

All use-case access is confined to **one module per adapter**, and that module
returns **domain entities, not DTOs**. The widgets receive `Project` and
`Task`. This is the single constraint that keeps a future change of access
strategy contained to one file instead of rippling through the interface, and
it costs nothing today: `infrastructure/db/repositories/` already reconstitutes
entities with the plain constructor, and any other implementation would do the
same. Reconstituting an entity is not re-validating it; the business rules run
where the use cases run.

### Two surfaces, mirroring the environment

Following the Omarchy split between one-shot commands and stateful TUIs, the
client exposes two surfaces over the same use cases:

- **The board** — a long-running full-screen Textual application for
  browsing, triaging and editing.
- **The capture prompt** — a single-line input, invoked from the window
  manager, that creates a task and exits without ever opening the board.
  It is a thin wrapper over the CLI, so the highest-frequency action costs no
  window and no context switch.

### Shell and module boundary

The Textual application is split into a generic **shell** (pane layout, focus
handling, modes, filtering, the command palette, the help overlay, undo, the
status bar) and a **module** that supplies the content of the three panes and
its own key bindings. Projects and Tasks are implemented as the first — and
currently only — module; the shell contains no Projects/Tasks-specific code.

The boundary is introduced now because retrofitting it into a hardcoded
single-module application is substantially more expensive than writing it
from the start. It is deliberately kept minimal: no module registry, module
switching, or cross-module navigation is designed until a second module
actually exists.

### User interface

The board is a three-pane layout — **context**, **collection**, **detail** —
navigated like Miller columns. For the Projects and Tasks module:

```
┌ life os ───────────────────────── local · 12 open · 3 overdue ─┐
│ PROJECTS         │ TASKS · life os · open  │ TASK              │
│ ▸ life os    12  │   ! port backend to tui │ write adr 0008    │
│   casa        3  │ ▸ ! write adr 0008      │ status   doing    │
│   learning    0  │   ◐ define keymap       │ priority high     │
│   finanzas    5  │   · add delete use case │ due      today    │
│   archivo     ·  │   ✓ mcp adapter         │ project  life os  │
│   + new project  │   · rename branch       │ created  jul 26   │
├──────────────────┴─────────────────────────┴───────────────────┤
│ NORMAL  /  a add  c done  d due  p prio  ^k palette  ? help    │
└────────────────────────────────────────────────────────────────┘
```

- **Context pane** — projects, with a count of open tasks, plus an inline
  entry for creating a new one.
- **Collection pane** — the tasks of the selected project, showing status
  glyph, priority marker, title and due date. Overdue dates are rendered in
  the error colour.
- **Detail pane** — a read-only preview of the selected task that becomes an
  editable form on `Enter`.
- **Status bar** — current mode, active filter, and the key hints for the
  focused pane.

Changing the selection in a pane updates the pane to its right; no pane
holds state that is invisible in the interface.

### Modality

The board is modal, in the vim sense, with the current mode always shown in
the status bar:

| Mode | Entered by | Purpose |
|---|---|---|
| `NORMAL` | default | navigation and single-key actions |
| `INSERT` | `a`, `e`, `d`, and other prompts | a text prompt is open; `Enter` commits |
| `FILTER` | `/` | live fuzzy filter over the focused pane |
| `SELECT` | `v`, `x` | multi-selection for bulk actions |
| `PALETTE` | `^k` | fuzzy command list overlay |

**`Esc` always goes back exactly one level** and never does anything else:
it closes the palette, clears a filter, cancels a prompt, or moves focus one
pane to the left; from the leftmost pane it prompts to quit. This mirrors the
`back_to` behaviour of `omarchy-menu`, where every submenu returns to its
parent and nothing else.

### Keymap

Digits are reserved for vim counts (`5j`, `3dd`) and are not bound to
actions. The `g` prefix is reserved for future navigation commands.

Global:

| Keys | Action |
|---|---|
| `h` `l` `Tab` `Shift+Tab` | move focus between panes |
| `j` `k` | move the cursor within the focused pane |
| `gg` `G` | first / last item |
| `^d` `^u` | half-page down / up |
| `/` | fuzzy filter the focused pane |
| `^k` | command palette |
| `?` | keybindings overlay |
| `u` `^r` | undo / redo the last write |
| `R` | reload from the database |
| `Esc` | back one level |
| `q` | quit |

Projects pane:

| Keys | Action |
|---|---|
| `a` | create a project (inline prompt) |
| `e` | rename |
| `Enter` `l` | focus the tasks pane |
| `c` | mark the project completed |
| `A` | archive / unarchive |
| `f` | filter by status |
| `dd` | delete, with confirmation |

Tasks pane:

| Keys | Action |
|---|---|
| `a` `o` | add a task through the quick-add prompt |
| `Enter` | open the detail form |
| `Space` | cycle status: todo → doing → done |
| `c` `s` `r` | complete / start / reopen |
| `e` | edit the title inline |
| `E` | edit the description in `$EDITOR` |
| `d` | set the due date |
| `p` | priority picker |
| `m` | move to another project |
| `x` `v` | toggle selection / bulk mode |
| `f` `S` | filter menu / cycle sort order |
| `y` | copy the task as markdown |
| `dd` | delete, with confirmation |

`Space` is bound to status cycling rather than the palette because it is the
most frequent action in the collection pane; the palette takes `^k`, the
common convention for command palettes in terminal applications.

### Single keymap registry

Every action is declared once, as a `(scope, key, label, use case)` entry in
a registry inside the TUI adapter. The command palette, the `?` overlay, and
the keymap documentation are all generated from it. This is the property that
makes Omarchy's menu maintainable — the menu is generated from the same
command metadata the commands themselves carry — and it is the only thing
preventing the bindings, the palette and the docs from drifting apart.

Consequently, **every keybinding is also reachable through the palette**:
the keyboard is the fast path, the palette is the discoverable path, and
neither is a subset of the other.

### Quick-add syntax

The `a` prompt accepts a single line with inline modifiers:

```
add › buy air filters !high @sat #casa
        └─ title ───┘ prio  due  project
```

- `!low` `!med` `!high` — priority
- `@today` `@tomorrow` `@fri` `@2026-08-03` — due date
- `#project` — target project, defaulting to the selected one
- everything else — the title

The `+` sigil is left unused and reserved for tags, so that adding them later
does not require redefining a syntax already in muscle memory.

The parser lives in the adapter and produces the arguments of
`CreateTask.execute`. It introduces no concept the domain does not already
have; the domain is not aware the syntax exists.

### Destructive actions and undo

Deletion is **soft**: `DeleteTask` and `DeleteProject` set a `deleted_at`
timestamp rather than removing rows, and every query excludes soft-deleted
records by default. `dd` still asks for confirmation, and `u` restores.

This is chosen over hard deletion because restoring a hard-deleted entity is
the one genuinely expensive undo case — `Task.create()` and `Project.create()`
generate their own identifiers, so a restore would need a dedicated
reconstruction path in the application layer. Soft deletion turns that into a
field flip, and has the independent benefit that a personal system never
silently loses data. Its cost is a filter condition in every list and get
operation, which must be applied in the repositories rather than left to
callers.

Undo covers the writes made during the current session: the adapter keeps the
previous entity state for the last N writes and replays the inverse call.
It is not a persistent history, and it is not an event log — it does not
survive restarting the board.

### Database configuration

Because [0007-shared-database-location.md](0007-shared-database-location.md)
makes every entry point converge on one file by default, concurrent access is
the normal case rather than an accident: the board, an MCP server spawned by
an agent, and a REST process can all hold it open at once. `session.py`
currently sets `foreign_keys=ON` but leaves the rollback journal in place and
`busy_timeout` at zero, so any contention raises `database is locked`
immediately instead of waiting. Enabling WAL journalling and a non-zero
`busy_timeout` is therefore a prerequisite of this adapter.

### Forward compatibility

Remote and multi-device access stay open questions for the desktop-app ADR
described above. Three constraints are kept here simply because they are free
today and expensive to retrofit:

- Use-case access is confined to one module per adapter, returning domain
  entities (above).
- MCP tool registration stays transport-agnostic — `register_tools()` takes a
  server instance and knows nothing about stdio, so the transport remains a
  single choice in `adapters/mcp/server.py`.
- Adapters are classified as either **colocated** (calling use cases in
  process, deployed with the application layer) or **remote** (speaking HTTP
  to it). Today REST, MCP, TUI and CLI are all colocated. A future adapter
  that cannot be colocated — a browser frontend is the obvious case — is
  remote by nature, and that difference, not a preference for uniformity, is
  what decides it.

### Application-layer work this requires

The interface described above cannot be built on the current use cases. The
following is completed **before** the adapter is built, and — being use cases
— becomes available to REST and MCP at the same time. Most of it exposes
domain behaviour that already exists but that no use case reaches.

| Needed for | Application-layer work |
|---|---|
| `Space`, `s`, `r` | `StartTask`, `ReopenTask` — mirroring `Task.start()` and `Task.reopen()`, alongside the existing `CompleteTask` |
| `c`, `A` on projects | `CompleteProject`, `ArchiveProject`, `ActivateProject` — mirroring the existing `Project` methods |
| `e` on projects | `UpdateProject` (rename, description) |
| `m` | `MoveTask`, plus a `Task.move_to()` transition in the domain |
| `dd` and `u` | `DeleteTask`, `DeleteProject`, `RestoreTask`, `RestoreProject`; `deleted_at` on both entities; exclusion of soft-deleted records in the repositories |
| detail pane | `GetTask`, `GetProject` |
| overdue views, `/`, palette search | `ListTasks` with an optional project plus status, due-date and text filters; `ListProjects` with status and text filters; matching port methods |

Cross-module search, as described in
[../vision.md](../vision.md#agent-access-model), is not built here — with one
module it is indistinguishable from the filtered listings above. It becomes a
real use case when a second module exists.

Sorting and the open-task counts are computed in the adapter from the results
of these use cases; at single-user data volumes this needs no dedicated query.

## Consequences

- Life OS becomes usable without an agent or an HTTP client, which is what
  Phase 1 of [../roadmap.md](../roadmap.md) requires from a CLI/TUI.
- The application-layer work is a substantial step in its own right, but it is
  pure application and domain work, testable with the existing in-memory fakes
  and with no interface present. It closes real gaps in the REST and MCP
  surfaces, which today cannot delete anything, cannot modify a project,
  cannot move a task, and cannot reach the `doing` state.
- Treating the TUI as the reference client means feature parity across
  adapters is the default rather than an aspiration: a capability cannot be
  added to the terminal without existing as a use case first.
- Because the client runs in process against SQLite, it cannot reach data on
  another machine. That is consistent with Life OS being a desktop app, but it
  does mean multi-device access — the Android app in Phase 6 — needs an answer
  this ADR does not provide.
- Several processes may write the same SQLite file, which ADR 0007 makes the
  default rather than the exception. WAL and `busy_timeout` make that safe,
  but there is no cross-process invalidation: the board must reload rather
  than assume its view is authoritative — hence `R`, and hence no long-lived
  caches in the adapter.
- Soft deletion adds a field to both entities and a filter to every read path.
  Forgetting that filter in a new repository method surfaces deleted records,
  so it belongs in the repositories, not in the use cases.
- Deferring tags and subtasks keeps this step small, at the cost of a second
  pass over the domain, the ports and the quick-add parser when they arrive.
  Reserving the `+` sigil now limits the interface half of that cost.
- The keymap registry adds one indirection over binding keys directly to
  handlers, in exchange for the palette, the help overlay and the docs never
  drifting from the bindings.
- The shell/module split costs a small amount of structure that a
  single-module application does not strictly need today, and is accepted as
  the cheaper moment to pay for it.
- Committing to a vim-style modal interface trades discoverability for speed.
  The palette and the `?` overlay are the mitigation, and both are mandatory
  rather than optional extras.
- The quick-add parser is adapter-local surface area that must be tested like
  any other input parsing, and must stay in sync with the fields of `Task` as
  the entity grows.

## Alternatives considered

- **A web frontend as the first human interface.** Phase 1 of the roadmap also
  mentions a minimal frontend. It was not chosen because it requires the REST
  server to be running, cannot be driven end to end from the keyboard without
  significant work, and does not fit the target desktop environment. It is
  deferred to a later step, not rejected; nothing here prevents it, since it
  would be one more adapter over the same use cases.
- **Routing the TUI through HTTP so that it and a future web frontend share
  one access path.** Rejected. The shared path already exists
  one layer down — both would call the same use cases either way (ADR 0002) —
  so HTTP adds a transport rather than reuse, and it makes a local application
  depend on a running server. A browser has no alternative to HTTP; a local
  terminal client does, and uniformity alone is not worth the added failure
  mode. What would force the change is data living on another machine — the
  multi-device question left open above — not the existence of a web frontend.
- **A CLI only, with no TUI.** Cheaper, and it would cover the capture flow
  completely, but triage over a list of tasks — the actual daily use — is
  poorly served by re-running commands and re-reading output.
- **A non-modal TUI with plain single-key actions.** Simpler to learn and to
  implement, but it forecloses counts, bulk selection and an unambiguous
  `Esc`, all of which are the reason the interface is fast once learned.
- **Hard deletion with a confirmation and no undo.** The smallest possible
  backend, but it makes `dd` unrecoverable in a system holding personal data,
  and it removes `u` from the keymap for the one action that most needs it.
- **Including tags and subtasks in this step.** Closer to the module described
  in [../vision.md](../vision.md), but subtasks in particular turn the
  collection pane from a flat list into a tree with indentation, completion
  rollup and its own navigation keys — a large increase in scope for the first
  version of an interface whose value is not yet proven in daily use.
- **Digits bound to actions, `g`/`G` to first/last.** An earlier version of
  this design; rejected because it conflicts with vim counts and with `gg`,
  which would make the keymap unlearnable for anyone who already uses vim
  motions.
