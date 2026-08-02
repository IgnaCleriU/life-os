# 0003. Manual project ordering

- ADR: [adr/0009-sqlite-migration-strategy.md](../adr/0009-sqlite-migration-strategy.md)

## Problem

Projects list in whatever order the database happens to return them
(effectively creation order) — no way to choose or persist a different
order. Life OS tracker task `f7ea8a62` asks for one, via dedicated TUI
keys: move the selected project up/down, each keypress committed and
undoable immediately, no confirmation step.

## Design

### Domain

`Project` gets a new field, `position: int`. No new domain *method* for
swapping — that needs two entities at once (the moved project and its
neighbor), which is an application-layer concern, not a single entity's.
`Project.create()` takes `position` as a required argument (the entity
doesn't know how many other projects exist, so it can't default it
itself).

### Application

Two use cases, `ReorderProjectUp` and `ReorderProjectDown` — mirroring the
existing one-verb-per-transition convention (`CompleteTask`, `StartTask`,
`ReopenTask` are three use cases, not one `SetTaskStatus(status)`; same for
`CompleteProject`/`ArchiveProject`/`ActivateProject`). Each takes only
`project_id`:

- Load all live projects via `ProjectRepository.list()` (now ordered by
  `position`), find the given project's index.
- If there's a neighbor in the requested direction, swap `position`
  between the two and persist both via `repo.update()`.
- If already at the boundary (first project moving up, last moving down),
  no-op — idempotent, consistent with `CompleteTask`/etc.
- Raise `ProjectNotFound` if the id doesn't resolve, same as every other
  single-project use case.

**Named "Reorder", not "Move"**, deliberately: `MoveTask` already exists
and means "change which project a task belongs to." Reusing "move" for
"change position within the list" would collide in meaning even though the
routes/tools don't collide in name.

`CreateProject.execute()` (`application/use_cases/create_project.py`)
computes the new project's position — `max(existing positions, default=-1)
+ 1` (append at the end) — before calling `Project.create(name,
description, position=...)`. Using max+1 rather than a live count avoids
any issue from soft-deleted projects leaving gaps in the position
sequence; gaps are fine, `position` only needs to sort correctly, not be
contiguous.

### Infrastructure

- `ProjectRepository.list()`'s SQLite implementation
  (`infrastructure/db/repositories/sqlite_project_repository.py`) adds
  `.order_by(ProjectModel.position)` to `_live()` — the single place every
  read goes through, so every existing caller (REST, MCP, CLI, TUI, and
  the domain-agnostic filters) gets position-ordered results automatically.
- `models.py`'s `ProjectModel` gains a `position: int` column.
- `session.py`'s `create_db_and_tables()` gains the one migration ADR 0009
  describes: check `PRAGMA table_info(projects)` for a `position` column;
  if absent, `ALTER TABLE projects ADD COLUMN position INTEGER`, then
  backfill it in Python from each row's current `created_at` order
  (enumerate projects ordered by `created_at`, `UPDATE` each row's
  `position` to its index).
- The in-memory fake `ProjectRepository` used by use-case unit tests
  (`backend/tests/application/fakes.py`) needs the same `position` field
  and ordering behavior — use-case tests never touch SQLite, so this fake
  is where `ReorderProjectUp`/`Down`'s own tests actually run.

**Migration is inherently untestable through the normal test fixtures** —
every test fixture builds a fresh in-memory SQLite DB via
`SQLModel.metadata.create_all()` against the *current* model definition,
which already includes `position` once this ships; the "column missing"
branch never executes through that path. It needs one dedicated test that
manually creates a table without the column, then asserts the migration
function adds it and backfills correctly.

### REST / MCP / CLI / TUI (parity, per ADR 0002)

Two endpoints/tools/commands each, no request body/parameter beyond the id
— mirroring `POST /tasks/{id}/complete`'s shape, not `POST
/tasks/{id}/move`'s (which takes a body):

| Layer | Addition |
|---|---|
| REST | `POST /projects/{id}/reorder-up`, `POST /projects/{id}/reorder-down` → `ProjectResponse` (gains a `position: int` field, mirrors the domain field like every other `*Response` schema) |
| MCP | `reorder_project_up(project_id)`, `reorder_project_down(project_id)` tools; `_project_dict()` gains `position` |
| CLI | `lifeos project reorder-up <id>`, `lifeos project reorder-down <id>` |
| TUI | Capital `K` (up) / `J` (down) in the CONTEXT (projects) scope keymap — free today, no collision with the existing lowercase `j`/`k` global cursor bindings or `gg`/`G` |

TUI action shape (`modules/projects_tasks.py`), mirroring
`_complete_project`'s no-prompt immediate-action pattern exactly: read
`shell.current_context_item`, call the use case, `_push_undo` (undo = call
the opposite-direction use case on the same id — a swap is its own
inverse, no need to snapshot/restore raw position values), then
`shell.action_reload()`.

### Known simplification (not fixed here)

`ReorderProjectUp`/`Down` swap within the **full** live project list, not
whatever subset the projects pane's `f` status filter currently shows. If
a filter is active, the swap partner might be a project that's currently
filtered out of view — the visible list won't appear to change. Reordering
scoped to the active filter is a real enhancement but a materially harder
problem (positions would need to mean different things depending on
view state); deferred rather than solved speculatively.

## Implementation tasks

| # | Task | Notes |
|---|---|---|
| 1 | `docs/adr/0009-sqlite-migration-strategy.md`, this spec (+ both READMEs' indexes) | Done as part of landing this spec. |
| 2 | `Project.position: int`; `Project.create()` takes `position` | Domain. |
| 3 | Fake `ProjectRepository` in `tests/application/fakes.py`: add `position`, order `list()` by it | Needed before use-case tests can run. |
| 4 | `CreateProject.execute()` computes `max(positions)+1` | Application. |
| 5 | `ReorderProjectUp`, `ReorderProjectDown` use cases | Application — new files under `application/use_cases/`. |
| 6 | `ProjectModel.position` column; SQLite repo `_live()` adds `ORDER BY position`; migration in `create_db_and_tables()` | Infrastructure. |
| 7 | REST: `ProjectResponse.position`, two new routes, deps wiring | `adapters/rest/`. |
| 8 | MCP: `_project_dict()` gains `position`, two new tools, deps wiring | `adapters/mcp/`. |
| 9 | CLI: two new commands | `adapters/cli/project_commands.py`. |
| 10 | TUI: `K`/`J` keymap entries + immediate-action methods | `adapters/tui/modules/projects_tasks.py`. |

## Open questions

None blocking. Filter-scoped reordering (see Known simplification) is a
future enhancement, not an open question for this spec.
