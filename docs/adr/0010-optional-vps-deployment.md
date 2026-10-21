# 0010. Optional VPS deployment over SSH

- Status: Accepted
- Date: 2026-10
- Amends: [0009-quickshell-desktop-client.md](0009-quickshell-desktop-client.md) ("nothing hosted and no remote access")
- Guide: [../deployment.md](../deployment.md)
- Superseded in part by: [0012-java-api-over-tailscale.md](0012-java-api-over-tailscale.md) (REST transport: Tailscale instead of an SSH tunnel)

## Context

ADR 0009 made Life OS a local desktop app with nothing hosted. Running
it on a server is now wanted too, as a deployment target that is
reachable away from the desktop and as preparation for remote clients
(Phase 6). The REST adapter already has what a hosted copy needs to be
safe. It refuses every route except `/health` without a bearer token,
and it checks `Host`. The Docker image and Compose file still build and
run. The data is still sensitive. The first host is an Azure for
Students subscription, which only allows five regions and blocks most
small VM sizes in some of them, Brazil South included. Capacity for the
sizes it does allow is not guaranteed either.

## Decision

Support an **optional VPS deployment** next to the local desktop app,
using the existing Docker image. Do not replace the desktop app.

- **Transport:** the API binds to `127.0.0.1` on the VPS
  (`deploy/vps/compose.override.yml`). The only open port is SSH,
  restricted to the operator's IP. Clients use an SSH tunnel for REST,
  and `ssh … docker compose exec -T backend lifeos-mcp` for MCP. No
  public HTTP port, TLS, or reverse proxy.
- **Auth:** the same per-install token as ADR 0009. The bootstrap
  generates one on the VPS, and it lives only in the VPS's `.env`.
- **Provisioning:** a provider-agnostic, idempotent cloud-init
  (`deploy/vps/cloud-init.yaml`). The repository is public, so the VPS
  clones it without credentials.
- **Azure tooling:** `deploy/azure/lifeos-vm.sh` handles create, start,
  stop, the tunnel and the SSH allow-list. It falls back to other region
  and size pairs when creating the VM, to other sizes when starting it,
  and to a disk copy into another region (`relocate`) when a whole region
  is out of capacity. The VM is deallocated every day at 01:00
  Argentina time.
- **Data:** the VPS has **its own SQLite database** in the `lifeos-data`
  volume. It is not synced with the desktop database (ADR 0007).

## Consequences

- There is a hosted instance that can be reached from anywhere SSH can,
  and none of the code or the auth model changed to get it.
- There are now two databases that do not know about each other.
  Choosing which one is canonical, or syncing them, is deferred to
  Phase 6.
- Personal data now lives on third-party hardware. The VM's disk is
  encrypted at rest by the provider, but the provider is trusted.
- Running costs about USD 0.45/day while the VM is on most of the day.
  Disk and IP are paid even while it is deallocated (about USD 0.27/day).
- A deallocated VM can fail to start when its region runs out of
  capacity. The size fallback and `relocate` mitigate this, but
  `relocate` changes the VM's IP and name.

## Alternatives considered

- Public HTTPS port with a reverse proxy: more moving parts and a larger
  attack surface than one client needs. Revisit for Phase 6.
- Tailscale instead of SSH tunnels: needs an extra install on every
  client. SSH is already there.
- A Raspberry Pi at home (ADR 0005's old leaning): no hardware for it
  today.
