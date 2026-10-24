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

# TUI reference

The `lifeos-tui` board and the `lifeos-capture` quick-add prompt call the
same use cases as the REST API, the MCP server, and the `lifeos` CLI (see
[../ARCHITECTURE.md](../ARCHITECTURE.md) and
[adr/0002-mcp-consumes-use-cases.md](adr/0002-mcp-consumes-use-cases.md)),
wired in process through `adapters/tui/deps.py` — no server needs to be
running. Both are **colocated driver adapters** in the sense of
[adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md),
which this document assumes you've read for the design rationale (the
shell/module split, why the client is modal, why deletion is soft).

## 1. Install and run

From `backend/`:

```bash
uv sync --all-extras
```

This registers the `lifeos-tui` and `lifeos-capture` console scripts (see
`[project.scripts]` in `backend/pyproject.toml`). Both create the SQLite
tables if they don't exist yet, then run.

```bash
uv run lifeos-tui         # the board: browse, triage, edit
uv run lifeos-capture "buy air filters !high @sat #casa"   # one task, no board
```

Like every other client, no `DATABASE_URL` is needed for normal use: the
TUI shares the same `~/.local/share/life-os/lifeos.db` as the REST API, the
MCP server, and the CLI (see
[../ARCHITECTURE.md](../ARCHITECTURE.md#where-the-data-lives)).

**If you're upgrading from before Steps 9-10**, delete and let `lifeos-tui`
recreate `~/.local/share/life-os/lifeos.db` first — that schema change
added `deleted_at` to both tables, and there is no migration tooling yet.
An old database file will crash the board with `no such column:
projects.deleted_at` on the very first render. **This deletes every
project and task currently stored in it** — back up the file first if it
holds real data you care about.

## 2. The board: panes and modes

Three panes, navigated like Miller columns — **PROJECTS** (context),
**TASKS** (collection), **TASK** (detail) — plus a status bar showing the
current mode, active filter, last action, and any error. Selecting a
project narrows the tasks pane; selecting a task fills the detail pane.
Nothing is ever true only in your head: changing a selection always
updates the pane to its right.

Five modes, one always active: **NORMAL** (navigation, single-key
actions), **INSERT** (a text prompt is open — quick-add, rename, due
date), **FILTER** (`/`, live substring filter), **SELECT** (`x`/`v`, bulk
multi-selection), **PALETTE** (`^k`, the fuzzy command list). `Esc` always
goes back exactly one level: it cancels a prompt, clears a filter, exits
select mode, or moves focus one pane to the left — never more, never less,
and never anything else. From the leftmost pane it quits directly (the
same as `q` — a confirmation dialog here is more machinery than this
interface needs yet).

Every binding below is also reachable through the command palette (`^k`) —
the keyboard is the fast path, the palette is the discoverable one, and
neither is a subset of the other. Press `?` any time for the full
keybindings overlay, generated from the same registry as the palette and
this table, so none of the three can silently drift from each other.

## 3. Global keymap

| Keys | Action |
|---|---|
| `h` `l` `Tab` `Shift+Tab` | move focus between panes |
| `j` `k` | move the cursor within the focused pane |
| `gg` `G` | first / last item |
| `^d` `^u` | half-page down / up |
| `/` | live substring filter over the focused pane |
| `^k` | command palette |
| `?` | keybindings overlay |
| `u` `^r` | undo / redo the last write |
| `R` | reload from the database |
| `Esc` | back one level |
| `q` | quit |

## 4. Projects pane

| Keys | Action |
|---|---|
| `a` | create a project (inline prompt) |
| `e` | rename |
| `Enter` `l` | focus the tasks pane |
| `c` | mark the project completed |
| `A` | archive / activate (toggles by current status) |
| `f` | filter by status (active / completed / archived / all) |
| `dd` | delete, with confirmation — fails with `project_not_empty` while the project still has live tasks |

## 5. Tasks pane

| Keys | Action |
|---|---|
| `a` `o` | add a task through the quick-add prompt |
| `Enter` | open the detail form |
| `Space` | cycle status: todo → doing → done → todo |
| `c` `s` `r` | complete / start / reopen |
| `e` | edit the title inline |
| `E` | edit the description in `$EDITOR` (falls back to `vi`) |
| `@` | set the due date — same syntax as quick-add's `@` (`sat`, `tomorrow`, `2026-08-03`) |
| `p` | priority picker (low / medium / high) |
| `m` | move to another project (picker over project names) |
| `x` `v` | toggle selection for the current item (bulk mode) |
| `f` `S` | filter by status / cycle sort order (created → due date → priority → created) |
| `y` | copy the task as a Markdown checkbox line to the system clipboard |
| `dd` | delete, with confirmation |

`d` is not bound on its own — see
[specs/0001-keyboard-driven-tui-adapter.md](specs/0001-keyboard-driven-tui-adapter.md#keymap)
for why (it collided with `dd`, and due date moved to `@` instead, which
already means "due date" in quick-add).

**Bulk mode:** press `x` or `v` on one or more tasks to select them, then
`c` or `dd` acts on every selected task at once (one combined undo entry,
not one per task) instead of just the currently-highlighted one.

## 6. Quick-add syntax

The `a`/`o` prompt in the tasks pane and `lifeos-capture` parse the exact
same syntax — see [cli.md#4-quick-add-syntax](cli.md#4-quick-add-syntax)
for the full reference (`!low`/`!med`/`!high`, `@today`/`@tomorrow`/
weekday/ISO dates, `#project`, the reserved `+tag` sigil, and the
degrade-to-literal-text rule for malformed tokens). The tasks pane defaults
an omitted `#project` to whichever project is currently selected, not to
an "inbox" project — `lifeos-capture`, run outside the board, keeps the
CLI's inbox-fallback behavior instead, since there's no selected project
to default to.

## 7. Undo and redo

Deletion is soft everywhere (projects and tasks): `dd` sets a timestamp,
it doesn't remove the row, and `u` undoes it by clearing that timestamp,
not by re-creating anything. Every other write (status transitions,
renames, due date, priority, moves, description edits) captures the prior
value before writing, so `u` restores exactly that value and `^r` re-applies
the write. Undo history covers the current session only — it is not a
persistent log and does not survive restarting the board.

## 8. `$EDITOR` and the clipboard

`E` suspends the board, opens `$EDITOR` (or `vi` if unset) on a temporary
file seeded with the task's current description, and reads it back once
the editor exits — the board redraws exactly where it left off. `y` copies
a Markdown checkbox line (`- [ ] title` or `- [x] title`, with the due
date appended if set) to the system clipboard over OSC 52, so it works
over SSH too, with no extra clipboard tooling required.

## 9. Omarchy keybindings

The primary interface is now the Omarchy board, not this TUI (see
[desktop.md](desktop.md) and
[adr/0009-quickshell-desktop-client.md](adr/0009-quickshell-desktop-client.md)).
The TUI stays as the terminal/SSH fallback. On Omarchy 4, whose Hyprland
config is Lua, bind it next to the board:

```lua
o.bind("SUPER + ALT + T", "Life OS (terminal)", { tui = "lifeos-tui" })
```

The examples below are for Omarchy 3's `hyprland.conf` syntax. They are a
starting point, not a verified config, so check them against your actual
Hyprland setup before relying on them.

`~/.config/hypr/bindings.conf` (or wherever your custom binds live):

```
# Full board, following the same launch-or-focus pattern as Impala/bluetui
bind = SUPER, T, exec, omarchy-launch-or-focus-tui "lifeos-tui" lifeos-tui

# One-shot capture from a Walker/dmenu-style prompt
bind = SUPER, A, exec, walker --dmenu --placeholder "capture..." | xargs -r lifeos-capture
```

Adjust the modifier/key to whatever isn't already bound, and swap `walker`
for whatever one-shot launcher your Omarchy config actually uses if it
differs — the ADR's own reference point is `omarchy-menu` (built on Walker
in dmenu mode) for one-shot commands and `omarchy-launch-or-focus-tui` for
full-screen terminal UIs like this one.

## 10. See also

- [adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md) —
  the ADR defining the shell/module split, the keymap, quick-add, and
  soft-delete/undo.
- [cli.md](cli.md) — the non-interactive counterpart, sharing the quick-add
  parser and every use case.
- [mcp-setup.md](mcp-setup.md) — the equivalent reference for the MCP
  adapter.
- [../ARCHITECTURE.md](../ARCHITECTURE.md) — layer boundaries and where the
  shared database lives.
