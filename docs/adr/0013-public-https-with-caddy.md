# 0013. Public HTTPS for the VPS API, behind Caddy

- Status: Accepted
- Date: 2026-10
- Supersedes: the transport part of [0012-java-api-over-tailscale.md](0012-java-api-over-tailscale.md) ("Tailscale Serve, no public port"). SSH stays for administration and MCP.
- Guide: [../deployment.md](../deployment.md#public-https)

## Context

ADR 0012 reaches the Java API over Tailscale, so every client needs the
Tailscale app and a tailnet login before it can open the web app or call the
API. The goal now is easy access: open `https://lifeos.ignacleri.dev/app/` from
any browser or device and log in with the token. The domain comes free for a
year from the GitHub Student Pack (name.com). The Java guard already has what
a public host needs: the bearer token with fail-closed behavior, the Host
allowlist (`LIFEOS_ALLOWED_HOSTS`), and relative redirects for a proxy that
terminates TLS.

## Decision

- **Transport:** a Caddy container on the VPS listens on TCP 443 for
  `LIFEOS_PUBLIC_HOST` and proxies to `backend-java:8000` over the compose
  network, keeping the original `Host`. It gets a Let's Encrypt certificate
  through the TLS-ALPN challenge, so port 80 stays closed. The NSG opens 443
  to any source. Port 22 stays restricted to the operator's IP.
- **Opt-in:** Caddy runs under the compose profile `public`
  (`COMPOSE_PROFILES=public` in the VPS's `.env`). Without it, the deploy is
  the loopback-only one from 0010/0012. The loopback port `127.0.0.1:8000`
  stays for the SSH tunnel.
- **No code change.** The domain is added to `LIFEOS_ALLOWED_HOSTS`; the token
  stays the only credential. No rate limiting: the token is 256 random bits.
- **Pinned image:** Caddy is pinned by tag and digest. Its certificates live
  in a named volume so the nightly deallocation does not re-issue them.
- **Tailscale is dropped** from the guide. Python still publishes no port.

## Consequences

- Any device reaches the web app and the API with a valid certificate, with
  nothing to install. The token is still required on every route except
  `/health` and the static web (`/`, `/app/**`).
- **The token is the only barrier between the internet and the data.** A
  leaked token is a full compromise until it is rotated. On the VPS,
  `LIFEOS_API_AUTH=disabled` now means open to the internet, so it must never
  be set there. A missing token still fails closed.
- `/health`, the web bundle and the TLS endpoint are visible to scanners.
  Logs will show probing traffic.
- The URL is down from 01:00 (nightly deallocation) until the VM is started
  by hand. `relocate` changes the IP: the DNS record and the 443 rule must be
  redone for the new VM.
- Let's Encrypt and name.com DNS join the access path.

## Alternatives considered

- Keep Tailscale (0012): every client needs the app and a login, which is
  what this decision removes.
- HTTPS restricted to the operator's IP: breaks on mobile data and other
  networks, the same problem as SSH.
- A custom domain inside the tailnet (DNS-01 via the name.com API): a nicer
  name, but still needs Tailscale on every client.
- Tailscale Funnel: public as well, but ties the URL to `*.ts.net` and the
  public path to Tailscale's relay.
