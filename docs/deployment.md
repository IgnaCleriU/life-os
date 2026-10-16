# Deploying Life OS on a VPS

Life OS is primarily a local desktop app (ADR 0009). It can also run on a VPS,
as described in [ADR 0010](adr/0010-optional-vps-deployment.md). This guide
covers how to do that: first the generic setup that works on any provider,
then the Azure tooling used for the current deployment.

## What runs where

```
your PC ──ssh (22, your IP only)──▶ VPS
   │                                 └─ docker compose: backend (uvicorn)
   └─ localhost:8000 ◀─tunnel──────────── 127.0.0.1:8000
                                          volume lifeos-data → /app/data/lifeos.db
```

- **Only port 22 is open, and only from your IP.** The API listens on the
  VPS's loopback (`deploy/vps/compose.override.yml`). You reach it through
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

### Daily credit check

[`deploy/vps/credit-check/`](../deploy/vps/credit-check/) holds a
stdlib-only Python script that checks how much Azure credit is left. It runs
every day at 12:00 Argentina time (`lifeos-credit-check.timer`). If the VM
was deallocated at that time, `Persistent=true` runs it right after the next
boot.

- **Where the result goes:** it logs to the journal
  (`journalctl -u lifeos-credit-check`), at warning priority when the
  balance is below `LIFEOS_CREDIT_THRESHOLD` (USD 10 by default). It also
  writes `/var/lib/lifeos/credit.json`
  (`{balance, currency, threshold, low, checked_at}`). That file is what
  the web and Android apps will read to notify devices.
- **Installation:** the cloud-init bootstrap installs it. The timer stays
  off until you fill in `/etc/lifeos/credit-check.env` with your billing
  profile scope. To find it, run:

  ```sh
  az billing account list --query "[].name" -o tsv              # <account>
  az rest --method get --url "https://management.azure.com/providers/Microsoft.Billing/billingAccounts/<account>/billingProfiles?api-version=2024-04-01" --query "value[].name" -o tsv   # <profile>
  ```

- **Permissions, a one-time step you run yourself.** The script
  authenticates with the VM's managed identity, so there are no secrets on
  disk. That identity needs read-only access to billing. Run this from your
  machine:

  ```sh
  PID=$(az vm identity assign -g rg-lifeos -n vm-lifeos --query systemAssignedIdentity -o tsv)
  BP=/providers/Microsoft.Billing/billingAccounts/<account>/billingProfiles/<profile>
  az rest --method post --url "https://management.azure.com$BP/createBillingRoleAssignment?api-version=2024-04-01" \
    --body "{\"principalId\":\"$PID\",\"principalTenantId\":\"$(az account show --query tenantId -o tsv)\",\"roleDefinitionId\":\"$BP/billingRoleDefinitions/40000000-aaaa-bbbb-cccc-100000000002\"}"
  ```

  The role ID ending in `…0002` is *Billing profile reader*. Until this is
  done, each run fails with `Identity not found`.

- **Tests:** they run without network, with
  `cd backend && uv run pytest ../deploy/vps/credit-check`.

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

- **Logs:** `docker compose logs -f backend`.
- **Rotate the token:** change `LIFEOS_API_TOKEN` in `.env`, then run
  `docker compose up -d`.
