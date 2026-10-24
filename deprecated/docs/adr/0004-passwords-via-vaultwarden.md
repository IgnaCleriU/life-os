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

# 0004. Password/vault storage approach

- Status: Proposed
- Date: 2026-07

## Context

The Passwords/Vault module (Phase 5 of the [roadmap](../roadmap.md)) is the
most sensitive module in Life OS: it stores credentials, not just personal
data. Rolling custom cryptography is a well-known way to introduce
security vulnerabilities, so the default bias should be toward reusing a
proven, audited solution rather than building one from scratch — unless
there is a specific reason to.

This module does not block the MVP (Projects + Tasks) and is scheduled for
a later phase, so the decision can remain open while other modules are
built.

## Decision

Not yet decided. Two options are on the table:

**Option A (recommended):** Integrate **Vaultwarden** (an open-source
implementation of the Bitwarden server API) as a separate service in the
deployment. The Life OS backend and MCP server talk to Vaultwarden's API
to list/create/update vault entries instead of storing passwords in the
Life OS database directly.

**Option B:** Build a self-contained vault with field-level AES-256
encryption, using a key derived from a master password via Argon2id. The
derived key is never stored server-side (only held transiently, e.g., in
the client session).

## Consequences

### If Option A is chosen
- Inherits battle-tested, production-grade encryption and existing client
  apps (browser extensions, mobile) for free.
- Adds an extra service to operate and back up (Vaultwarden + its own
  data volume), and an extra integration surface (its API) for the
  backend/MCP adapters to consume — consistent with ADR 0002, MCP would
  still go through Life OS use cases, which in turn call Vaultwarden's
  API rather than a local repository.
- Life OS effort stays focused on building value in its own modules
  instead of re-solving a problem the industry has already solved well.

### If Option B is chosen
- Everything lives under one schema/one deployment, avoiding a second
  service.
- Considerably more implementation and review effort, and higher risk if
  the crypto or key-handling has subtle flaws — only justified if
  learning the cryptography is itself a goal of the project, per the
  original evaluation in the development guide.
- Requires a clear answer for key derivation, session handling, and what
  happens if the master password is lost, before any code is written.

### Regardless of option
- Whatever is chosen, MCP tools for this module must go through explicit,
  non-default-on permission checks (see
  [../../ARCHITECTURE.md](../../ARCHITECTURE.md) and the agentic-workflow
  doc) — AI agents should not read or write vault entries without
  explicit, deliberate authorization.

## Alternatives considered

- **Store passwords as plain encrypted columns in the main Life OS DB
  without field-level per-entry keys:** rejected outright — weaker than
  both options above and offers no real advantage.
- **Rely on an external password manager the user already has (no Life OS
  integration at all):** keeps Life OS out of the sensitive path entirely,
  but drops the "single system an AI agent can act on" value proposition
  for this module; not pursued further for now.
