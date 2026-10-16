# 0011. Port the backend core and REST adapter to Java + Spring Boot

- Status: Proposed
- Date: 2026-10

## Context

The backend core (domain, application, SQLite infrastructure) and every
adapter are written in Python ([0006-tech-stack.md](0006-tech-stack.md)).
The decision is to move the backend to Java and Spring Boot. The work is
staged: domain, application, infrastructure and REST go first. The MCP
server, the CLI and the TUI stay in Python until a later step decides
where they go.

## Decision

Build a Java 21 + Spring Boot backend under `backend-java/`, alongside
`backend/`, as a Maven multi-module project with one module per hexagonal
layer (`domain`, `application`, `infrastructure`, `adapter-rest`). `domain`
and `application` stay framework-free: Spring is not on their classpath,
so the build enforces the dependency rule ([0001](0001-hexagonal-monorepo.md)).
Persistence uses plain JDBC (`JdbcClient` + `sqlite-jdbc`), not JPA.

The Java REST adapter is a drop-in for the Python one: same routes, JSON
shape, status codes, and error codes.

## Consequences

- **Until the cutover, two implementations of the use cases share one
  database** ([0007](0007-shared-database-location.md)): Python (MCP, CLI,
  TUI) and Java (REST). Both must read each other's rows. Java therefore
  writes the exact storage format SQLAlchemy uses (naive-UTC
  `yyyy-MM-dd HH:mm:ss.SSSSSS` text, lowercase enum values, UUID strings),
  and a cross-implementation test guards it.
- Java only writes the columns it knows about (explicit column lists, plain
  `UPDATE`), so columns that other branches add (e.g. `position`,
  recurrence) survive.
- Business rules exist twice during the transition, so a rule change has
  to land in both until Python's core is removed.
- Schema creation mirrors Python's idempotent `create_all`. Migration
  tooling is still pending.
- Python's REST adapter and its tests stay in place until the Java one
  replaces it.

## Alternatives considered

- Spring Data JPA/Hibernate: there is no first-party SQLite dialect, and
  JPA entities would blur the infrastructure boundary.
- Flyway now: it would write its history table into the real personal
  database, and that database's schema already differs between branches.
