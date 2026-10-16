# Deploying Life OS on a VPS

Life OS is primarily a local desktop app (ADR 0009). It can also run on a VPS,
as described in [ADR 0010](adr/0010-optional-vps-deployment.md). This guide
covers how to do that: first the generic setup that works on any provider,
then the Azure tooling used for the current deployment.

## What runs where

```
your PC ──ssh (22, your IP only)──▶ VPS
   │                                 ├─ backend-java (Spring Boot) ◀── published API
   │                                 └─ backend (uvicorn)  ◀── MCP only, no port
   └─ localhost:8000 ◀─tunnel──────────── 127.0.0.1:8000
                                          volume lifeos-data → /app/data/lifeos.db
```

- **Only port 22 is open, and only from your IP.** The API (the Java
  backend, [ADR 0012](adr/0012-java-api-over-tailscale.md)) listens on the
  VPS's loopback (`deploy/vps/compose.override.yml`). The Python container
  keeps running for MCP but publishes no port. You reach it through
  an SSH tunnel.
- **Every route except `/health` needs `Authorization: Bearer <token>`.**
  The token is generated on first boot and lives only in `~/life-os/.env`
  on the VPS.
- **The VPS has its own database, separate from the one on your desktop.**
  Nothing syncs them.

## Any provider: cloud-init

Create an Ubuntu 24.04 x64 VM (1 GB of RAM is enough) with:

- SSH key authentication only, with the admin user `azureuser`. If your
  user has another name, change the `runcmd` argument in the file.
- [`deploy/vps/cloud-init.yaml`](../deploy/vps/cloud-init.yaml) as the
  user-data / custom-data.
- A firewall that allows only TCP 22 from your IP.

cloud-init installs Docker and clones the repo into `~/life-os`. Then it
copies the compose override, writes `.env` with a fresh token, and runs
`docker compose up -d --build`. The whole thing takes about 10 minutes on
a small VM. To check on it, run `cloud-init status --wait` on the VPS.

The bootstrap (`/opt/lifeos/bootstrap.sh`) is idempotent. An existing
checkout or `.env` is left alone, so you can run it again safely.

## Azure

[`deploy/azure/lifeos-vm.sh`](../deploy/azure/lifeos-vm.sh) wraps the
`az` CLI. It needs `pacman -S azure-cli` and `az login`. The defaults
match the current deployment, and every one of them can be overridden
with an environment variable (`LIFEOS_RG`, `LIFEOS_VM`, `LIFEOS_SSH_KEY`,
`LIFEOS_CANDIDATES`, `LIFEOS_FALLBACK_SIZES`, `LIFEOS_SHUTDOWN_UTC`, …).

| Command | What it does |
|---|---|
| `create` | Creates the VM from the first `region:size` pair in `LIFEOS_CANDIDATES` that the subscription allows. It also restricts SSH to your IP and schedules the daily shutdown. |
| `start` | Starts the VM. If the region lacks capacity for the current size, it resizes to the next size in `LIFEOS_FALLBACK_SIZES` and retries. |
| `stop` | Deallocates the VM, which stops compute billing. |
| `status` | Prints power state, region, size and IP. |
| `tunnel [port]` | Forwards `localhost:<port>` (default 8000) to the API. |
| `allow-ip` | Points the SSH rule at your current public IP. Run it when your home IP changes. |
| `relocate REGION [SIZE]` | Last resort when a whole region has no capacity. It snapshots the disk, copies it to `REGION` and boots a new VM from that disk, so the data comes along. |

You need the SSH key `~/.ssh/lifeos-azure`. Generate it with
`ssh-keygen -t ed25519 -f ~/.ssh/lifeos-azure`.

### Daily use

```sh
deploy/azure/lifeos-vm.sh start
deploy/azure/lifeos-vm.sh tunnel            # leave it running
TOKEN=$(ssh -i ~/.ssh/lifeos-azure azureuser@<ip> 'grep ^LIFEOS_API_TOKEN= ~/life-os/.env | cut -d= -f2')
curl -H "Authorization: Bearer $TOKEN" localhost:8000/projects
```

The VM is **deallocated every day at 01:00 Argentina time** (04:00 UTC).
Nothing starts it again on its own: run `start` when you need it.

To use MCP against the VPS, point the MCP client at this command:

```sh
ssh -i ~/.ssh/lifeos-azure azureuser@<ip> docker compose -f life-os/docker-compose.yml exec -T backend lifeos-mcp
```

### Why these regions and sizes

Azure for Students allows only `brazilsouth`, `northcentralus`,
`canadacentral`, `southafricanorth` and `newzealandnorth`. In Brazil
South, the subscription is blocked from every small B-series size
(`NotAvailableForSubscription`), and the smallest D/F sizes run into
quota limits. The default candidates are the cheapest x64 sizes that
passed Azure's preflight validation (October 2026):

| Region | Size | Linux USD/h |
|---|---|---|
| northcentralus | Standard_B2ats_v2 (2 vCPU, 1 GB) | 0.0094 |
| southafricanorth | Standard_B2ats_v2 | 0.0122 |
| newzealandnorth | Standard_B2ats_v2 | 0.0125 |

Availability changes over time. `create` and `relocate` check the
subscription's SKU restrictions before they try a region.

### Costs

| | While running | While deallocated |
|---|---|---|
| Compute (B2ats_v2, northcentralus) | ~USD 0.23/day | 0 |
| Standard SSD 32 GB | ~USD 0.15/day | ~USD 0.15/day |
| Standard public IP | ~USD 0.12/day | ~USD 0.12/day |

A VM that is shut down from inside (`sudo shutdown`) is *stopped*, not
deallocated, and **its compute is still billed**. Use `stop` or the
portal's Stop button instead.

## Phone access over Tailscale

[ADR 0012](adr/0012-java-api-over-tailscale.md). An Android phone can't
open an SSH tunnel comfortably, so the VPS joins a Tailscale tailnet and
`tailscale serve` publishes the loopback API as HTTPS **inside the tailnet
only**. The port 22 rule still holds: no public port is added, and nothing
is exposed through Tailscale Funnel.

1. Install Tailscale on the VPS and join the tailnet:

   ```sh
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. In the Tailscale admin console, enable **MagicDNS** and **HTTPS
   Certificates** (DNS page). Install Tailscale on the phone and sign in to
   the same tailnet.
3. Publish the API to the tailnet over HTTPS:

   ```sh
   sudo tailscale serve --bg --https=443 http://127.0.0.1:8000
   tailscale serve status
   ```

4. Allow the tailnet names in the API. `tailscale serve` forwards the
   original `Host` header, which the Host check would otherwise refuse. In
   `~/life-os/.env` on the VPS:

   ```sh
   LIFEOS_ALLOWED_HOSTS=<machine>,<machine>.<tailnet>.ts.net
   ```

   Then recreate the containers: `cd ~/life-os && docker compose up -d`.
5. Check it from another device in the tailnet:

   ```sh
   curl -i https://<machine>.<tailnet>.ts.net/health            # 200, no token
   curl -i https://<machine>.<tailnet>.ts.net/projects          # 401
   curl -i -H "Authorization: Bearer <token>" https://<machine>.<tailnet>.ts.net/projects   # 200
   ```

The bearer token is still required on every route except `/health`. The
phone app must send `Authorization: Bearer <token>`, with the token from the
VPS's `.env`. A VM that is deallocated daily (see Azure above) is unreachable
until it is started again, and `tailscale` reconnects by itself on boot.

## Operating the VPS

- **Update the app:** run
  `cd ~/life-os && git pull && docker compose up -d --build`.
- **Back up the database.** SQLite's online backup is safe while the API
  is running:

  ```sh
  cd ~/life-os
  docker compose exec -T backend python -c "import sqlite3; s=sqlite3.connect('/app/data/lifeos.db'); d=sqlite3.connect('/app/data/backup.db'); s.backup(d); d.close()"
  docker compose cp backend:/app/data/backup.db ./lifeos-backup.db
  ```

- **Logs:** `docker compose logs -f backend-java` (the API) or
  `docker compose logs -f backend` (Python, MCP).
- **Rotate the token:** change `LIFEOS_API_TOKEN` in `.env`, then run
  `docker compose up -d`.
