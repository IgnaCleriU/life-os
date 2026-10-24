> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](../DEPRECATED.md).

# Deploying Life OS on a VPS

Life OS is primarily a local desktop app (ADR 0009). It can also run on a VPS,
as described in [ADR 0010](adr/0010-optional-vps-deployment.md). This guide
covers how to do that: first the generic setup that works on any provider,
then the Azure tooling used for the current deployment.

## What runs where

```
your PC ──ssh (22, your IP only)──▶ VPS
   │                                 ├─ backend-java (Spring) ── 127.0.0.1:8000
   └─ localhost:8000 ◀─tunnel────────┤                     ▲
any device ──HTTPS (443, public)─────┤   caddy ────────────┘  (profile `public`)
                                     └─ backend (Python, MCP only, no port)
                                        volume lifeos-data → /app/data/lifeos.db
```

- **Port 22 is open only from your IP. Port 443 is open to everyone** once
  you enable public HTTPS ([ADR 0013](adr/0013-public-https-with-caddy.md),
  below). The Java API (`backend-java`) listens on the VPS's loopback
  (`deploy/vps/compose.override.yml`); Caddy is the only thing that reaches
  it from outside. The Python `backend` publishes no port; it stays for MCP.
- **Every route except `/health` and the web app (`/`, `/app/`) needs
  `Authorization: Bearer <token>`.** The token is generated on first boot and
  lives only in `~/life-os/.env` on the VPS. With public HTTPS it is the only
  barrier between the internet and your data: **never set
  `LIFEOS_API_AUTH=disabled` on a VPS.**
- **The VPS has its own database, separate from the one on your desktop.**
  Nothing syncs them.

## Any provider: cloud-init

Create an Ubuntu 24.04 x64 VM (1 GB of RAM is enough) with:

- SSH key authentication only, with the admin user `azureuser`. If your
  user has another name, change the `runcmd` argument in the file.
- [`deploy/vps/cloud-init.yaml`](../deploy/vps/cloud-init.yaml) as the
  user-data / custom-data.
- A firewall that allows only TCP 22 from your IP. Open TCP 443 to everyone
  only when you enable [public HTTPS](#public-https).

cloud-init adds a 2 GB swapfile (`/swapfile`, swappiness 10) so a 1 GB VM
does not run out of memory, installs Docker and clones the repo into
`~/life-os`. Then it
links the compose override, writes `.env` with a fresh token, and runs
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
| `open-https` | Opens TCP 443 to any source, for [public HTTPS](#public-https). |
| `close-https` | Removes that rule. Use it to cut access at once if the token leaks, then rotate it. |
| `relocate REGION [SIZE]` | Last resort when a whole region has no capacity. It snapshots the disk, copies it to `REGION` and boots a new VM from that disk, so the data comes along. The new VM has a new IP: update the DNS record and run `open-https` with `LIFEOS_VM` set to it. |

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

## Public HTTPS

[ADR 0013](adr/0013-public-https-with-caddy.md). Caddy listens on 443 for your
domain, gets a Let's Encrypt certificate and proxies to the Java API. Port 80
stays closed: the certificate comes through the TLS-ALPN challenge on 443.
The current deployment uses `lifeos.ignacleri.dev`.

1. **DNS:** an `A` record for the domain pointing at the VM's public IP
   (`deploy/azure/lifeos-vm.sh status`). Check it with
   `resolvectl query <domain>` before going on: Caddy can't get a certificate
   until the name resolves to the VM.
2. **Firewall:** `deploy/azure/lifeos-vm.sh open-https` (or open TCP 443 on
   your provider).
3. **VPS `.env`** (`~/life-os/.env`): add these lines. If
   `LIFEOS_ALLOWED_HOSTS` already exists, append the domain to it with a
   comma instead of adding a second line.

   ```sh
   COMPOSE_PROFILES=public
   LIFEOS_PUBLIC_HOST=<domain>
   LIFEOS_ALLOWED_HOSTS=<domain>
   ```

   Then run `cd ~/life-os && git pull && docker compose up -d`.
   `docker compose logs -f caddy` shows the certificate being issued
   ("certificate obtained successfully").
4. **Verify, every time you change the deploy.** Do not skip this: it is the
   check that the token still guards everything.

   ```sh
   curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/health                 # 200
   curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/projects               # 401
   curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" https://<domain>/projects   # 200
   curl -s -o /dev/null -w '%{http_code}\n' https://<vm-ip>/health                  # 000: no certificate for a bare IP
   ```

**Clients:** open `https://<domain>/app/` in any browser and paste the token
(the `LIFEOS_API_TOKEN` line of `~/life-os/.env`) in the login screen. Other
clients use `https://<domain>` as the server URL.

**If Caddy fails to start** with "failed to bind host port 0.0.0.0:443":
something else holds 443 on the VM (`sudo ss -ltnp 'sport = :443'`). On the
current VM it was `tailscale serve`, left from ADR 0012; turn it off with
`sudo tailscale serve --https=443 off`. Then run
`docker compose up -d --force-recreate caddy`: the container left by the
failed start has no ports and no working DNS, so the certificate request
fails with "lookup … on 127.0.0.53:53: connection refused".

**If the token leaks:** run `close-https` first, then rotate the token (see
below) and `open-https` again.

The URL is down from 01:00, when the VM is deallocated, until you run
`start`. Caddy keeps its certificates in the `caddy-data` volume, so a restart
does not request new ones.

## Operating the VPS

- **Update the app:** run
  `cd ~/life-os && git pull && docker compose up -d --build`.
  The build now compiles the Java image with Maven, which may run out of
  memory on a 1 GB VM even with the swapfile (not tried). If it does, build
  on your machine
  (`docker build -t life-os-backend-java:latest backend-java`), send it with
  `docker save life-os-backend-java:latest | gzip | ssh <vps> 'gunzip | docker load'`
  and run `docker compose up -d --no-build`.
- **Back up the database.** SQLite's online backup is safe while the API
  is running:

  ```sh
  cd ~/life-os
  docker compose exec -T backend python -c "import sqlite3; s=sqlite3.connect('/app/data/lifeos.db'); d=sqlite3.connect('/app/data/backup.db'); s.backup(d); d.close()"
  docker compose cp backend:/app/data/backup.db ./lifeos-backup.db
  ```

- **Logs:** `docker compose logs -f backend-java` (the API), `caddy` (HTTPS) or `backend`
  (Python, MCP).
- **Rotate the token:** change `LIFEOS_API_TOKEN` in `.env`, then run
  `docker compose up -d`.
