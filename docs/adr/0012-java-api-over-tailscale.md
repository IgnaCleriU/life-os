# 0012. Java API as the VPS API, reached over Tailscale

- Status: Proposed
- Date: 2026-10
- Amends: [0010-optional-vps-deployment.md](0010-optional-vps-deployment.md) (transport), [0011-java-spring-backend.md](0011-java-spring-backend.md) ("loopback only, no token")
- Guide: [../deployment.md](../deployment.md#phone-access-over-tailscale)

## Context

ADR 0010 reaches the VPS with an SSH tunnel, which an Android phone can't
do comfortably. The Java adapter from ADR 0011 is meant to replace the
Python REST adapter, but it lacked what makes a hosted copy safe: the
bearer token, the configurable Host allowlist and a bind address other than
loopback. Without them it could not be the published API.

## Decision

- **Java is the published API on the VPS.** `LocalGuardFilter` ports
  `auth.py`: every route except `/health` needs `Authorization: Bearer
  <token>` (constant-time comparison), the `Host` header is checked first,
  and an enabled guard with no token fails closed with 401. It reads the same
  variables as Python: `LIFEOS_API_TOKEN`, `LIFEOS_API_AUTH` and
  `LIFEOS_ALLOWED_HOSTS`. As in Python, `LIFEOS_API_AUTH=disabled` turns the
  whole guard off, Host check included.
- **Bind address:** `server.address` comes from `LIFEOS_BIND_ADDRESS`,
  loopback by default. Only the Docker image sets `0.0.0.0`; the published
  port stays `127.0.0.1:8000` on the host.
- **Containers:** `backend-java` shares the `lifeos-data` volume and `.env`
  with `backend`. On the VPS only Java publishes a port. Python keeps
  running without one, because MCP still enters through
  `docker compose exec backend lifeos-mcp`.
- **Transport for the phone:** Tailscale on the VPS, with `tailscale serve`
  providing HTTPS from the loopback port to the tailnet. No public port is
  opened, port 22 stays the only one, and Funnel is not used.

## Consequences

- The phone reaches the API with a valid TLS certificate, and only devices
  in the tailnet can connect. The token is still required on top.
- Two backends write one SQLite file from separate containers. That is the
  situation ADR 0011 already accepts, now on the VPS too.
- The guard exists twice until Python's REST adapter is removed, so a change
  to it has to land in both.
- Tailscale is a new third-party dependency in the access path, and its
  coordination server is trusted to authorize devices. The VPS needs the
  Tailscale install and login done by hand (documented, not in cloud-init).
- Locally, the Python API stays on port 8000 and Java is on 8001, so the
  desktop board is unaffected.

## Alternatives considered

- Keep the Python adapter published and use Java later: the cutover then
  needs the same work, and the phone would hit the code being replaced.
- Public HTTPS with a reverse proxy: rejected for the same reasons as in ADR
  0010, plus certificates and an open port.
- Tailscale Funnel: would expose the API to the internet, which the token
  alone should not be trusted to carry.
- SSH tunnel apps on Android: workable, but fragile on mobile networks.
