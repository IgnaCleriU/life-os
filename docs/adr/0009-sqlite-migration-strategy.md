# 0009. Ad-hoc idempotent migrations for local SQLite schema changes

- Status: Accepted
- Date: 2026-08

## Context

No migration tooling exists yet. The only schema change so far
(`deleted_at` on both tables, roadmap Step 9) was handled by telling
whoever hit it to delete `~/.local/share/life-os/lifeos.db` and let the
app recreate it empty. That's no longer acceptable: the db now holds real
personal data, and CLAUDE.md forbids deleting it without explicit
confirmation. A second schema change (a `position` column on `projects`,
for manual ordering) is about to land, and the roadmap's later phases
(Notes, Calendar, Home inventory, Passwords) will keep adding
tables/columns over time.

## Decision

Handle schema evolution with small, idempotent, guarded migration checks
run from `create_db_and_tables()` in `infrastructure/db/session.py` — the
one function REST, MCP, CLI, and the TUI already all call before touching
the database. Each migration checks whether its target already exists (via
`PRAGMA table_info` for a column, `sqlite_master` for a table) and, if not,
applies it — nothing else. No migration framework (e.g. Alembic) is
adopted.

## Consequences

- Existing data survives schema changes automatically, on every adapter,
  with no manual step from whoever's running the app.
- No rollback, no versioned migration history, no down-migrations —
  accepted at single-user scale, where schema changes are rare and
  reviewed by hand before merging.
- Each migration is hand-written and must itself stay idempotent and cheap
  to check on every process start.
- Does not scale to frequent or complex schema changes. If that becomes
  the actual pattern, revisit and adopt a real migration tool then — this
  ADR is deliberately the minimum that unblocks the current need, not a
  long-term bet.

## Alternatives considered

- **Alembic (or similar framework)**: standard practice, but adds a
  dependency, a separate migration-file workflow, and ceremony
  disproportionate to a single-user local app with schema changes this
  infrequent so far.
- **Keep "delete and recreate"**: rejected — destroys real user data,
  which CLAUDE.md now explicitly forbids without confirmation.
