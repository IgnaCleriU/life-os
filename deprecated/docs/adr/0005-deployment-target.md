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

# 0005. Deployment target

- Status: Superseded by [0009](0009-quickshell-desktop-client.md)
- Date: 2026-07
- Deprecated: 2026-07
- Superseded: 2026-09

> **Deprecated.** Life OS is being built as a **native TUI desktop
> application for Omarchy**, launching the backend and the TUI together on
> the user's own machine. That makes the framing below obsolete: it treats
> deployment as a hosting question (where does a server run, how is it
> reached remotely) when the answer is now that there is no server to host
> — the app runs locally, like any other desktop program.
>
> Specifically no longer current:
> - **Docker Compose as the local runtime.** The Compose files remain in
>   the repo but are no longer the intended way to run Life OS day to day.
> - **The self-hosted Pi / mini-PC + Tailscale trajectory** as the assumed
>   next step once the system is used daily.
>
> What still holds is the underlying reasoning, not the conclusion: the
> data is sensitive and should stay on hardware the user owns. A native
> desktop app satisfies that more directly than any of the three options
> weighed below.
>
> Remote access and multi-device use (e.g. the Android app in Phase 6, see
> [../roadmap.md](../roadmap.md)) are *not* settled by this deprecation —
> they become open questions for the desktop-app ADR that supersedes this
> one. That ADR is [0009](0009-quickshell-desktop-client.md): a local
> REST daemon plus a Quickshell client, loopback-only, with remote access
> still deferred.
>
> The text below is kept unedited as the record of what was believed at the
> time; see [README.md](README.md) for why ADRs are not rewritten in place.

## Context

Life OS stores sensitive personal data (notes, passwords, home inventory)
and needs to be reachable from multiple clients over time (web frontend,
CLI/TUI, Android app, AI agents). Where the system runs affects auth
design, network exposure, and operational cost, so it is worth deciding
deliberately rather than defaulting into a choice.

Three deployment options were evaluated:

| Option | Advantages | Disadvantages |
|---|---|---|
| Self-hosted at home (e.g., Raspberry Pi / mini PC) | Full control, no recurring cost, data never leaves the home network | Needs a remote-access solution (VPN/Tailscale) to use outside the house or from the Android app |
| Own VPS (Hetzner, DigitalOcean, etc.) | Simple remote access, good availability | Monthly cost; sensitive data lives on a third-party server (mitigable with encryption) |
| Local only (PC/laptop) | Zero network configuration | No access from a phone unless on the same network; unsuitable for everyday "from anywhere" use |

## Decision

Not yet finalized. Current leaning, to be confirmed as the project
progresses:

- **For the MVP:** run everything with Docker Compose on a local
  development machine. No remote access, no additional network setup —
  this matches the current phase (Projects + Tasks only, single user,
  local iteration).
- **Later:** move to self-hosted at home (e.g., Raspberry Pi or mini PC)
  plus Tailscale (a free VPN mesh) once the system is usable day-to-day
  and Android/remote access are needed, avoiding exposing ports directly
  to the internet.

This is treated as the best balance of privacy, cost, and practicality for
a project handling sensitive personal data, but it remains open for
revision — particularly if a VPS turns out to be simpler to operate in
practice, or if the self-hosted option proves unreliable.

## Consequences

- MVP development proceeds without any deployment/network decisions
  blocking it (see [../roadmap.md](../roadmap.md), Phase 0).
- Auth design (JWT access/refresh, see
  [0006-tech-stack.md](0006-tech-stack.md)) is chosen to work reasonably
  under any of the three options, avoiding lock-in to one deployment
  target this early.
- The self-hosted + Tailscale path, if confirmed, avoids exposing the
  backend to the public internet, which is a meaningful security benefit
  given the sensitivity of the data (especially once the Passwords module,
  ADR 0004, exists).
- If a VPS is chosen instead, additional hardening (rate limiting, TLS,
  stricter auth) becomes necessary sooner, since the service would be
  reachable from the public internet.

## Alternatives considered

Covered above as the three evaluated options. No option has been ruled
out permanently; this ADR should be updated to Accepted once a target is
confirmed, and superseded if the decision changes after real usage.
