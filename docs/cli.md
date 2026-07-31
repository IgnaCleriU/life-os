# CLI reference

The `lifeos` command line calls the same use cases as the REST API and the
MCP server (see [../ARCHITECTURE.md](../ARCHITECTURE.md) and
[adr/0002-mcp-consumes-use-cases.md](adr/0002-mcp-consumes-use-cases.md)),
wired in process through its own `adapters/cli/deps.py` — no server needs to
be running. It is a **colocated driver adapter** in the sense of
[adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md),
and the non-interactive counterpart to the TUI board described there.

## 1. Install and run

From `backend/`:

```bash
uv sync --all-extras
```

This creates `.venv` with the exact versions pinned in `backend/uv.lock` and
registers the `lifeos` console script (see `[project.scripts]` in
`backend/pyproject.toml`), which runs
`lifeos.adapters.cli.main:main` — creates the SQLite tables if they don't
exist yet, then dispatches to the requested command.

```bash
uv run lifeos --help
uv run lifeos project --help
uv run lifeos task --help
```

No `DATABASE_URL` is needed for normal use: by default the CLI shares the
same `~/.local/share/life-os/lifeos.db` as the REST API and the MCP server
(see [../ARCHITECTURE.md](../ARCHITECTURE.md#where-the-data-lives)). Set
`DATABASE_URL` only to point at a different file (tests, or a scratch DB
for manual experiments).

## 2. Global `--json` flag

`--json` is a **root-level** option: it must come **before** the
subcommand, not after it.

```bash
lifeos --json project list      # correct
lifeos project list --json      # error: "No such option: --json" (exit 2)
```

This follows from how the flag is wired: it is parsed by the root `typer`
callback in `adapters/cli/main.py` and stashed on `ctx.obj["json"]`, before
any subcommand app (`project`, `task`, `capture`/`add`) even runs.

With `--json`, every command that emits an entity or a list of entities
prints one JSON value to stdout — a single object for `show`/`create`/etc.,
a JSON array for `list` (including an empty array `[]` when there are no
results). Without `--json`, the same commands print plain text: one line
per entity, whitespace-column-aligned, with no colors or box drawing — see
[Output format](#4-output-format-stdout-vs-stderr) below.

## 3. Command tree

### `project` — manage projects

| Command | Arguments | Options | Notes |
|---|---|---|---|
| `project create` | `name` | `--description` | |
| `project list` | — | `--status` (repeatable), `--text` | filters are ANDed; omit both to list everything |
| `project show` | `project_id` | — | |
| `project update` | `project_id` | `--name`, `--description`, `--clear-description` | omitted `--description` leaves it untouched; `--clear-description` clears it; the two are mutually exclusive; there is no `--clear-name` (the domain forbids empty names) |
| `project complete` | `project_id` | — | idempotent |
| `project archive` | `project_id` | — | idempotent |
| `project activate` | `project_id` | — | idempotent (reactivates) |
| `project delete` | `project_id` | `--yes`/`-y` | soft delete; prompts for confirmation unless `--yes`; fails with `project_not_empty` if the project still has live tasks |
| `project restore` | `project_id` | — | undoes `delete` |

### `task` — manage tasks

| Command | Arguments | Options | Notes |
|---|---|---|---|
| `task create` | `project_id`, `title` | `--priority` (`low`/`medium`/`high`, default `medium`), `--due` (ISO `YYYY-MM-DD`), `--description` | |
| `task list` | — | `--project` (id; all projects if omitted), `--status` (repeatable), `--due-before` (ISO date), `--text` | |
| `task show` | `task_id` | — | |
| `task update` | `task_id` | `--title`, `--description`, `--clear-description`, `--priority`, `--due`, `--clear-due` | same omit-vs-clear rules as `project update`; no `--clear-title` |
| `task complete` | `task_id` | — | idempotent |
| `task start` | `task_id` | — | moves to `doing` |
| `task reopen` | `task_id` | — | moves back to `todo`/pending |
| `task move` | `task_id`, `project_id` | — | moves the task to another existing project |
| `task delete` | `task_id` | `--yes`/`-y` | soft delete; prompts for confirmation unless `--yes` |
| `task restore` | `task_id` | — | undoes `delete` |

`--due` and `--due-before` take a plain ISO date (`YYYY-MM-DD`), **not** the
quick-add `@...` syntax below — that syntax is only understood by
`capture`/`add`.

### `capture` / `add` — quick-add a task

```bash
lifeos capture <free-form text>
lifeos add <free-form text>       # exact alias, same command
```

Both names are registered for the same handler in `adapters/cli/main.py`, so
they behave identically, including under `--json`.

## 4. Quick-add syntax

`capture`/`add` parses one line of free-form text into a task, using the
tokenizer defined in `adapters/shared/quick_add.py` and specified by
[adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md#quick-add-syntax).
It splits the text on whitespace (no regex) and recognizes these token
shapes, in any position, in any order:

| Sigil | Meaning | Recognized forms |
|---|---|---|
| `!` | Priority | `!low`, `!med`, `!high` |
| `@` | Due date | `@today`, `@tomorrow`, `@mon`..`@sun` (weekday abbreviation), `@YYYY-MM-DD` (ISO date) |
| `#` | Target project | `#name` — a single token, matched against an existing project name, exact and case-insensitive |
| `+` | Tag (reserved) | `+anything` — recognized, stripped from the title, and silently discarded |
| everything else | Title | free text |

```
lifeos add buy air filters !high @sat #casa
              └── title ──┘ prio  due  project
```

Semantics worth knowing before scripting against this:

- **Weekday resolution is strictly future.** `@mon`..`@sun` always resolve
  to the *next* occurrence of that weekday, never today — if today is
  Tuesday, `@tue` lands seven days out, not zero. (`@today`/`@tomorrow` are
  the explicit ways to mean "today" or "the next calendar day".)
- **`#project` is a single token and must match an existing project
  exactly** (case-insensitive, whitespace-trimmed). Project names with
  spaces cannot be targeted through quick-add. No match raises
  `project_name_not_found`; more than one active project sharing that name
  raises `ambiguous_project_name` and lists the candidate ids — in either
  case, disambiguate with `lifeos task create <project_id> ...` instead of
  `capture`.
- **No `#project` — the task lands in "inbox".** See
  [Inbox fallback](#5-inbox-fallback-and-its-race-caveat) below.
- **Duplicate sigils: last one wins.** `!low !high` resolves to `high`;
  there is no error, quick-add favors capture speed over strict
  correctness.
- **Malformed `!`/`@` tokens degrade to literal title text**, rather than
  failing the command. `!urgent` is not a recognized priority token, so it
  is left in the title verbatim; the same applies to a bare sigil (`!`,
  `@`, `#`, `+` with nothing after it) or an `@` token that doesn't match
  any of the recognized date forms (e.g. `@whenever`, `@2026-13-45`).
- **`+tag` is parsed and discarded, not stored.** The sigil is reserved for
  a future `tags` field (per ADR 0008); today it is only removed from the
  title so it doesn't pollute it.

Example:

```bash
$ lifeos --json capture "call plumber @whenever !urgent #inbox"
{"id": "...", "title": "call plumber @whenever !urgent", ...}
```

Here neither `@whenever` nor `!urgent` matched a recognized form, so both
stayed in the title as literal text, and `#inbox` resolved the project.

## 5. Inbox fallback and its race caveat

Quick-add text with no `#project` token targets a project literally named
`inbox` (case-insensitive exact match, same resolution as `#project`). If
no such project exists yet, `capture` creates it on the fly — so the first
`capture`/`add` without `#project` against a fresh database silently
creates an "inbox" project as a side effect.

This get-or-create has an accepted **TOCTOU race**: the app is single-user
and takes no explicit lock between checking whether "inbox" exists and
creating it, so two concurrent captures could theoretically both observe
"does not exist yet" and each create their own "inbox" project. This is
accepted because the real usage pattern is one user issuing commands
serially from a terminal; if it ever happens, it's recoverable by hand
(move the tasks out of the duplicate inbox and delete one of the two
projects). See the docstring of `adapters/cli/capture.py` for the full
reasoning.

## 6. Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Domain error — a mapped domain or CLI-resolution exception (not found, validation, non-empty project, ambiguous/unresolved project name). Printed to **stderr** as `<code>: <message>`, e.g. `project_not_found: ...`. |
| `2` | Usage error — bad arguments, unknown options, invalid UUIDs/enum values, `--yes` declined at a confirmation prompt. Handled by Click/Typer, not by Life OS's own error mapping. |

The exit-code-1 error codes come from `_DOMAIN_ERROR_CODES` in
`adapters/cli/errors.py`: `domain_validation_error`, `project_not_found`,
`task_not_found`, `project_not_empty`, `project_name_not_found`,
`ambiguous_project_name`.

## 7. Output format: stdout vs. stderr

- **stdout** carries only the command's result — either the plain-text
  line(s) or, under `--json`, exactly one JSON value (object or array) —
  making it safe to pipe into `jq` or another script without stripping
  anything:

  ```bash
  lifeos --json task list --status todo | jq -r '.[].title'
  ```

- **stderr** carries everything else: confirmation prompts (`project
  delete`/`task delete` without `--yes`), domain error lines
  (`<code>: <message>`), and Click/Typer usage errors.

- Plain-text `list` output is empty (no output, exit `0`) when there are no
  results; `--json list` output is `[]` in the same case.

## 8. Soft delete and restore

`project delete` and `task delete` are **soft**: they set a `deleted_at`
timestamp rather than removing the row, and every list/show excludes
deleted records by default. `project restore`/`task restore` undo it. Both
`delete` commands prompt for confirmation on a terminal; pass `--yes`/`-y`
to skip the prompt (e.g. for scripting).

## 9. Examples

```bash
# Create a project, then a task under it
PROJECT_ID=$(lifeos --json project create "casa" | jq -r .id)
lifeos task create "$PROJECT_ID" "buy air filters" --priority high --due 2026-08-01

# Quick-add straight into that project
lifeos add "buy air filters !high @sat #casa"

# Quick-add with no project — lands in the auto-created inbox
lifeos capture "water the plants !low @tomorrow"

# List open tasks across all projects as JSON, extract titles with jq
lifeos --json task list --status todo --status doing | jq -r '.[].title'

# Delete a task without a confirmation prompt, then undo it
lifeos task delete "$TASK_ID" --yes
lifeos task restore "$TASK_ID"
```

## See also

- [adr/0008-keyboard-driven-tui-adapter.md](adr/0008-keyboard-driven-tui-adapter.md) —
  the ADR defining the CLI/TUI split, the quick-add syntax, and soft-delete/undo.
- [mcp-setup.md](mcp-setup.md) — the equivalent reference for the MCP adapter,
  which exposes the same use cases over stdio instead of a terminal.
- [../ARCHITECTURE.md](../ARCHITECTURE.md) — layer boundaries and where the
  shared database lives.
