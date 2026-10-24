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

# Architecture Decision Records

This directory records the significant architectural and technical
decisions made for Life OS, using a lightweight MADR format (Context,
Decision, Consequences, and optionally Alternatives considered). Each
decision is captured once it is made, kept immutable, and superseded by a
new ADR if it later changes — rather than edited in place — so the
history of *why* the system looks the way it does stays legible over time.

**ADRs stay short — about one page.** They record the decision and why, not
the design or the implementation plan. When a decision needs UI mockups,
data flow, syntax, or a breakdown of implementation steps, that detail goes
in a paired document under [../specs/](../specs/README.md), linked from the
ADR's Status block.

For background on the overall system, see [../vision.md](../vision.md) and
[../../ARCHITECTURE.md](../../ARCHITECTURE.md). For the phased build plan,
see [../roadmap.md](../roadmap.md).

To propose a new decision, copy [0000-template.md](0000-template.md), give
it the next available number, and open a pull request.

## Index

| Number | Title | Status |
|---|---|---|
| [0001](0001-hexagonal-monorepo.md) | Monorepo with hexagonal architecture | Accepted |
| [0002](0002-mcp-consumes-use-cases.md) | MCP server consumes the same use cases as REST | Accepted |
| [0003](0003-sqlite-for-mvp-postgres-later.md) | SQLite for the MVP, PostgreSQL later | Accepted |
| [0004](0004-passwords-via-vaultwarden.md) | Password/vault storage approach | Proposed |
| [0005](0005-deployment-target.md) | Deployment target | Superseded by 0009 |
| [0006](0006-tech-stack.md) | Technology stack | Accepted |
| [0007](0007-shared-database-location.md) | One shared database in the user data directory | Accepted |
| [0008](0008-keyboard-driven-tui-adapter.md) | Keyboard-driven TUI adapter | Accepted |
| [0009](0009-quickshell-desktop-client.md) | Quickshell desktop client over a local REST daemon | Accepted |
| [0010](0010-optional-vps-deployment.md) | Optional VPS deployment over SSH | Accepted |
| [0011](0011-java-spring-backend.md) | Port the backend core and REST adapter to Java + Spring Boot | Proposed |
| [0012](0012-java-api-over-tailscale.md) | Java API as the VPS API, reached over Tailscale | Accepted; transport superseded by 0013 |
| [0013](0013-public-https-with-caddy.md) | Public HTTPS for the VPS API, behind Caddy | Accepted |
