> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../../../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](../../DEPRECATED.md).

# 0002. MCP server consumes the same use cases as REST

- Status: Accepted
- Date: 2026-07

## Context

The MCP server is the interface AI agents use to read and modify data in
Life OS. It would be technically simpler for MCP tools to query the
database directly, bypassing the REST adapter's code path. However, that
would create a second, parallel implementation of business rules
(validation, permissions, auditing) that could drift from the REST
implementation over time — a correctness and security risk, since MCP is
specifically the entry point used by autonomous or semi-autonomous agents.

## Decision

The MCP server does not access the database directly. Each MCP tool calls
the same `application/use_cases/` functions/classes that the REST adapter
calls (see [../../ARCHITECTURE.md](../../ARCHITECTURE.md)). REST and MCP
are two adapters over the same application layer; neither contains
business logic of its own — both only translate between their respective
protocols (HTTP/Pydantic DTOs vs. MCP tool schemas) and the use cases.

## Consequences

- Business rules, input validation, and audit logging are guaranteed to
  apply identically regardless of whether a request came from a human via
  the web frontend/CLI/Android app or from an AI agent via MCP.
- New use cases become available to agents automatically once exposed as
  an MCP tool — no logic needs to be reimplemented.
- MCP tool handlers stay thin: parse tool input, call a use case, format
  the result. This keeps them easy to audit, which matters given they are
  the surface exposed to AI agents.
- Requires the MCP adapter to authenticate/authorize like any other client
  of the application layer; it cannot take a shortcut around permission
  checks for convenience.
- Slightly more indirection than calling the DB straight from an MCP tool,
  but this is intentional overhead in exchange for a single source of
  truth for business rules.

## Alternatives considered

- **MCP reads directly from the database (read-only queries only):**
  rejected because even read paths may need to enforce permissions (e.g.,
  a future access policy that blocks agents from reading the Passwords
  module by default, see ADR 0004) — logic that lives in the application
  layer, not in raw queries.
- **Shared "service layer" separate from REST's own logic:** effectively
  the same idea as this decision, just named differently; the chosen
  wording aligns with the `application/use_cases/` layer already defined
  in [../../ARCHITECTURE.md](../../ARCHITECTURE.md).
