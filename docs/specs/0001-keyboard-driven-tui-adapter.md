# 0008. Keyboard-driven TUI adapter

- ADR: [adr/0008-keyboard-driven-tui-adapter.md](../adr/0008-keyboard-driven-tui-adapter.md)

## Problem

The forces behind the ADR's decision, in full:

- **A native desktop application, not a hosted service.**
  [../vision.md](../vision.md) targets one self-hosted user, and
  [0005-deployment-target.md](../adr/0005-deployment-target.md) has been
  deprecated precisely because it framed deployment as a hosting question:
  Life OS is being built as a native TUI desktop application for Omarchy,
  launching the backend and the interface together on the user's own
  machine. There is no server to reach and no remote client to design
  around.
- **One database, at a known absolute path.**
  [0007-shared-database-location.md](../adr/0007-shared-database-location.md)
  places the SQLite file in the user's data directory, so every entry point
  converges on the same data with no configuration — the property that
  makes an in-process client show exactly what the agent sees.
- **Keyboard-first environment.** The target desktop is Omarchy (Hyprland),
  where system settings are manipulated entirely by keyboard through two
  distinct surfaces: a narrow fuzzy menu for one-shot commands
  (`omarchy-menu`, built on Walker in dmenu mode) and full-screen terminal
  UIs for stateful domains (Impala for Wi-Fi, bluetui for Bluetooth,
  launched through `omarchy-launch-or-focus-tui`). Both surfaces are
  generated from small composable commands that carry their own metadata,
  so the menu is a discoverable mirror of the commands rather than a
  parallel implementation.
- **A narrow existing use-case surface.** The application layer exposed
  only `CreateProject`, `ListProjects`, `CreateTask`, `ListTasks`,
  `UpdateTask` and `CompleteTask`. No delete, no project mutation, no
  lookup by id, no way to move a task between projects, no way to reach
  the `doing` state, no way to list tasks outside a single project — even
  though the domain entities already implemented most of those
  transitions.
- **A deliberate build order.** The application layer is completed first,
  and the TUI is built against it afterwards. A web frontend is explicitly
  deferred to a later step.

Only Projects and Tasks exist as a domain module. The later modules
described in [../vision.md](../vision.md) are out of scope here.

### Scope

Within scope: the module surface is the Projects and Tasks entities **as
they exist today** — name, description, status, priority, due date. Tags
and subtasks, listed for this module in [../vision.md](../vision.md), are
deliberately not part of this step; deferred until the interface has been
in real use long enough to show whether they're missed.

Out of scope: how the application is packaged and launched, the
authentication decision Phase 0 leaves open (JWT was chosen for a
networked backend, which a local desktop app is not), and remote/
multi-device access for the Android app in Phase 6. Those belong to the
desktop-app ADR that 0005 is waiting to be superseded by; 0008 narrows the
interface question rather than answering those in passing, so 0005 stays
`Deprecated` and is not marked superseded by 0008.

## Design

### The TUI is the reference client

Because it is the only human interface, the TUI defines completeness for
the module: **every capability the system has for Projects and Tasks must
be reachable from it.** Anything not reachable from the TUI does not exist
for the user. Each capability is added as a use case first, so REST and
MCP gain it at the same time and at no extra cost.

### Access to the application layer

The TUI and CLI call use cases **in process**, wiring the SQLite
repositories through their own `deps.py`, the same way
`adapters/rest/deps.py` and `adapters/mcp/deps.py` do. They do not talk to
the REST API over HTTP.

This follows from Life OS being a desktop application rather than a hosted
service: there is no server to reach, so requiring one to be running would
be a constraint the design imposes on itself. Going through HTTP would not
increase reuse — the reuse already lives at the use-case layer, per ADR
0002 — it would only add a transport, an HTTP client, DTO deserialization,
and a mapping from status codes back to domain errors.

All use-case access is confined to **one module per adapter**, and that
module returns **domain entities, not DTOs**. The widgets receive
`Project` and `Task`. This is the single constraint that keeps a future
change of access strategy contained to one file instead of rippling
through the interface, and it costs nothing today:
`infrastructure/db/repositories/` already reconstitutes entities with the
plain constructor. Reconstituting an entity is not re-validating it; the
business rules run where the use cases run.

### Two surfaces, mirroring the environment

Following the Omarchy split between one-shot commands and stateful TUIs,
the client exposes two surfaces over the same use cases:

- **The board** — a long-running full-screen Textual application for
  browsing, triaging and editing.
- **The capture prompt** — a single-line input, invoked from the window
  manager, that creates a task and exits without ever opening the board.
  It is a thin wrapper over the CLI, so the highest-frequency action costs
  no window and no context switch.

### Shell and module boundary

The Textual application is split into a generic **shell** (pane layout,
focus handling, modes, filtering, the command palette, the help overlay,
undo, the status bar) and a **module** that supplies the content of the
three panes and its own key bindings. Projects and Tasks are implemented
as the first — and currently only — module; the shell contains no
Projects/Tasks-specific code.

The boundary is introduced now because retrofitting it into a hardcoded
single-module application is substantially more expensive than writing it
from the start. It is deliberately kept minimal: no module registry,
module switching, or cross-module navigation is designed until a second
module actually exists.

### User interface

The board is a three-pane layout — **context**, **collection**,
**detail** — navigated like Miller columns:

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
  glyph, priority marker, title and due date. Overdue dates are rendered
  in the error colour.
- **Detail pane** — a read-only preview of the selected task that becomes
  an editable form on `Enter`.
- **Status bar** — current mode, active filter, and the key hints for the
  focused pane.

Changing the selection in a pane updates the pane to its right; no pane
holds state that is invisible in the interface.

### Modality

The board is modal, in the vim sense, with the current mode always shown
in the status bar:

| Mode | Entered by | Purpose |
|---|---|---|
| `NORMAL` | default | navigation and single-key actions |
| `INSERT` | `a`, `e`, and other prompts | a text prompt is open; `Enter` commits |
| `FILTER` | `/` | live fuzzy filter over the focused pane |
| `SELECT` | `v`, `x` | multi-selection for bulk actions |
| `PALETTE` | `^k` | fuzzy command list overlay |

**`Esc` always goes back exactly one level** and never does anything else:
it closes the palette, clears a filter, cancels a prompt, or moves focus
one pane to the left; from the leftmost pane it prompts to quit. This
mirrors the `back_to` behaviour of `omarchy-menu`, where every submenu
returns to its parent and nothing else.

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
| `@` | set the due date |
| `p` | priority picker |
| `m` | move to another project |
| `x` `v` | toggle selection / bulk mode |
| `f` `S` | filter menu / cycle sort order |
| `y` | copy the task as markdown |
| `dd` | delete, with confirmation |

`d` is not bound on its own: `dd` (delete) and a single `d` (originally
due date, in the design as first accepted) would collide, since `d` is
simultaneously a complete binding and a strict prefix of `dd`. The
due-date picker moved to `@` instead, which already means "due date" in
the quick-add syntax below (`@sat`) — reusing it keeps the two surfaces
teaching the same mental model instead of introducing a second meaning
for `d`. This is the Step 12 amendment referenced in the ADR; a keymap
registry test now asserts no binding is a strict prefix of another unless
declared as such.

`Space` is bound to status cycling rather than the palette because it is
the most frequent action in the collection pane; the palette takes `^k`,
the common convention for command palettes in terminal applications.

### Single keymap registry

Every action is declared once, as a `(scope, key, label, use case)` entry
in a registry inside the TUI adapter. The command palette, the `?`
overlay, and the keymap documentation are all generated from it — the
same property that makes Omarchy's menu maintainable, and the only thing
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

The `+` sigil is left unused and reserved for tags, so that adding them
later does not require redefining a syntax already in muscle memory.

The parser lives in the adapter and produces the arguments of
`CreateTask.execute`. It introduces no concept the domain does not
already have; the domain is not aware the syntax exists.

### Destructive actions and undo

Deletion is **soft**: `DeleteTask` and `DeleteProject` set a `deleted_at`
timestamp rather than removing rows, and every query excludes soft-deleted
records by default. `dd` still asks for confirmation, and `u` restores.

Chosen over hard deletion because restoring a hard-deleted entity is the
one genuinely expensive undo case — `Task.create()` and `Project.create()`
generate their own identifiers, so a restore would need a dedicated
reconstruction path in the application layer. Soft deletion turns that
into a field flip, and has the independent benefit that a personal system
never silently loses data. Its cost is a filter condition in every list
and get operation, which must be applied in the repositories rather than
left to callers.

Undo covers the writes made during the current session: the adapter keeps
the previous entity state for the last N writes and replays the inverse
call. It is not a persistent history and not an event log — it does not
survive restarting the board.

### Database configuration

Because [0007-shared-database-location.md](../adr/0007-shared-database-location.md)
makes every entry point converge on one file by default, concurrent
access is the normal case rather than an accident: the board, an MCP
server spawned by an agent, and a REST process can all hold it open at
once. `session.py` set `foreign_keys=ON` but left the rollback journal in
place and `busy_timeout` at zero, so any contention raised `database is
locked` immediately instead of waiting. Enabling WAL journalling and a
non-zero `busy_timeout` is a prerequisite of this adapter.

### Forward compatibility

Remote and multi-device access stay open questions for the desktop-app
ADR described above. Three constraints are kept here because they are
free today and expensive to retrofit:

- Use-case access is confined to one module per adapter, returning domain
  entities (above).
- MCP tool registration stays transport-agnostic — `register_tools()`
  takes a server instance and knows nothing about stdio, so the transport
  remains a single choice in `adapters/mcp/server.py`.
- Adapters are classified as either **colocated** (calling use cases in
  process, deployed with the application layer) or **remote** (speaking
  HTTP to it). Today REST, MCP, TUI and CLI are all colocated. A future
  adapter that cannot be colocated — a browser frontend is the obvious
  case — is remote by nature, and that difference, not a preference for
  uniformity, is what decides it.

## Implementation tasks

The interface above could not be built on the use cases that existed when
this was written. The application-layer work below was completed
**before** the adapter, and — being use cases — became available to REST
and MCP at the same time. Most of it exposed domain behaviour that
already existed but that no use case reached yet.

| # | Task | Notes |
|---|---|---|
| 1 | `StartTask`, `ReopenTask` | Mirrors `Task.start()` / `Task.reopen()`, alongside the existing `CompleteTask`. Needed for `Space`, `s`, `r`. |
| 2 | `CompleteProject`, `ArchiveProject`, `ActivateProject` | Mirrors the existing `Project` methods. Needed for `c`, `A` on projects. |
| 3 | `UpdateProject` (rename, description) | Needed for `e` on projects. |
| 4 | `MoveTask` + `Task.move_to()` domain transition | Needed for `m`. |
| 5 | `DeleteTask`, `DeleteProject`, `RestoreTask`, `RestoreProject`; `deleted_at` on both entities; exclusion of soft-deleted records in repositories | Needed for `dd` and `u`. |
| 6 | `GetTask`, `GetProject` | Needed for the detail pane. |
| 7 | `ListTasks` with optional project + status/due-date/text filters; `ListProjects` with status/text filters; matching port methods | Needed for overdue views, `/`, palette search. |
| 8 | Board (Textual shell + Projects/Tasks module), CLI, quick-add parser, keymap registry, WAL + `busy_timeout` | The adapter itself, built on tasks 1-7. Delivered as roadmap Steps 9-13. |

Cross-module search, per [../vision.md](../vision.md#agent-access-model),
was not built here — with one module it is indistinguishable from the
filtered listings above (task 7). It becomes a real use case when a
second module exists.

Sorting and open-task counts are computed in the adapter from the results
of these use cases; at single-user data volumes this needs no dedicated
query.

All tasks above shipped as roadmap Steps 9-13 (see [../roadmap.md](../roadmap.md)) — this table is a historical record of the plan, not open work.

## Open questions

None remaining for the scope of this spec. Remote/multi-device access and
packaging are explicitly deferred to the desktop-app ADR superseding
[0005-deployment-target.md](../adr/0005-deployment-target.md), which is
still pending.
