# 0003. SQLite for the MVP, PostgreSQL later

- Status: Accepted
- Date: 2026-07

## Context

Life OS is currently single-user, running locally via Docker Compose, with
no requirement for concurrent multi-device write access. The MVP scope is
limited to the Projects + Tasks module. Setting up PostgreSQL from day one
adds operational overhead (a separate container, connection pooling,
credentials) that is not justified while the schema is still small and
changing frequently.

## Decision

Use SQLite as the database engine for the MVP. Migrate to PostgreSQL when
real multi-device or concurrent-access needs arrive (e.g., the Android app
or a self-hosted always-on deployment used from multiple clients at once,
see [0005-deployment-target.md](0005-deployment-target.md)).

The persistence layer is accessed exclusively through repository ports
defined in `application/ports/` (see
[../../ARCHITECTURE.md](../../ARCHITECTURE.md)), so the concrete engine is
an infrastructure-layer implementation detail — switching from SQLite to
PostgreSQL means adding a new repository implementation, not changing
domain or use-case code.

Alembic (migrations) is deferred: for the MVP, tables are created with
SQLModel's `create_all`. Alembic is introduced once the schema starts
changing often enough that manual recreation becomes risky (i.e., once
there is data worth preserving across schema changes).

## Consequences

- Zero extra infrastructure to run the MVP locally — one file, no separate
  DB container.
- SQLite's limited concurrent-write support is acceptable now (single
  user, single process) but is the trigger condition for the PostgreSQL
  migration.
- Migrating later is a scoped, additive change: implement
  `Postgres*Repository` classes against the existing ports, update
  `infrastructure/config.py` and Docker Compose, no domain/use-case
  changes required.
- Without Alembic, early schema changes are handled by dropping and
  recreating the SQLite file in development. This is acceptable only
  because there is no production data yet; Alembic must be in place before
  any deployment holds data worth preserving.

## Alternatives considered

- **PostgreSQL from day one:** more production-realistic, but adds
  container/credential overhead disproportionate to a single-user MVP with
  a still-changing schema.
- **Alembic from day one:** safer for schema evolution, but adds migration
  authoring overhead while the domain model (currently just Project/Task)
  is still being shaped; revisit once the schema stabilizes or before the
  first deployment with real data.
