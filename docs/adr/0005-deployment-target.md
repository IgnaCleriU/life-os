# 0005. Deployment target

- Status: Proposed
- Date: 2026-07

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
