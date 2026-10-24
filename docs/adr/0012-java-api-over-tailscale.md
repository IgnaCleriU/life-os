# 0012. Java API as the VPS API, reached over Tailscale

- Status: Accepted; transport superseded by [0013](0013-public-https-with-caddy.md)
- Date: 2026-10
- Supersedes: the transport part of [0010-optional-vps-deployment.md](0010-optional-vps-deployment.md) ("SSH tunnel for REST, no TLS or reverse proxy"). SSH stays for administration and MCP.
- Amends: [0011-java-spring-backend.md](0011-java-spring-backend.md) (the Java adapter now has the token and Host allowlist)
- Guide: [../deployment.md](../deployment.md#phone-access-over-tailscale)

## Context

ADR 0010 reaches the VPS through an SSH tunnel, which a phone can't do
comfortably, and the web and Android clients need the Java API
([0011](0011-java-spring-backend.md)) over HTTPS. The Java adapter now ports
what makes a hosted copy safe: the bearer token, the configurable Host
allowlist and a configurable bind address.

## Decision

- **Java is the published API on the VPS.** `LocalGuardFilter` ports `auth.py`:
  every route except `/health` needs `Authorization: Bearer <token>`
  (constant-time comparison), `Host` is checked first, and an enabled guard
  with no token fails closed. It reads `LIFEOS_API_TOKEN`, `LIFEOS_API_AUTH`
  and `LIFEOS_ALLOWED_HOSTS`, like Python.
- **Bind address:** `LIFEOS_BIND_ADDRESS`, loopback by default. Only the
  Docker image sets `0.0.0.0`; the host port stays `127.0.0.1:8000`.
- **Containers:** `backend-java` and `backend` share the `lifeos-data` volume
  and `.env`. On the VPS only Java publishes a port; Python keeps running for
  MCP (`docker compose exec backend lifeos-mcp`).
- **Transport:** Tailscale on the VPS; `tailscale serve` terminates HTTPS and
  proxies to the loopback port, for tailnet devices only. No public port is
  opened (22 stays the only one) and Funnel is not used.

## Consequences

- Phone and laptop reach the API with a valid certificate; only tailnet
  devices can connect, and the token is still required.
- Two backends write one SQLite file from separate containers, the situation
  0011 already accepts.
- The guard exists twice until the Python REST adapter is removed.
- Tailscale is a new third-party dependency in the access path (its
  coordination server authorizes devices). Install and login on the VPS are
  manual, not in cloud-init.
- Locally nothing changes: Python on 8000, Java on 8001.

## Alternatives considered

- Keep Python published and move to Java later: same cutover work, and the
  clients would hit the code being replaced.
- Public HTTPS with a reverse proxy: rejected for the reasons in 0010, plus
  certificates and an open port.
- Tailscale Funnel: exposes the API to the internet; the token alone should
  not carry that.
- SSH tunnel apps on Android: workable but fragile on mobile networks.
