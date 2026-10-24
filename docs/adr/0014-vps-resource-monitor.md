# 0014. VPS resource monitor: Beszel on the web, CSV files on the VM

- Status: Accepted
- Date: 2026-10
- Guide: [../deployment.md](../deployment.md#resource-monitor)

## Context

The VPS has 887 MB of RAM. It hung once with no swap, and nothing showed what
was using the memory. The operator wants two things: a web view of resource
use that can be checked from any device, and plain files on the VM that can
be read or copied without any tool. The web view sits on the public domain
from [ADR 0013](0013-public-https-with-caddy.md), so it must have its own
login and must never be reachable without an owner.

## Decision

- **Web: [Beszel](https://beszel.dev)** (hub + agent, about 15 MB of RAM
  together). It has its own login, history per host and per container, and
  alerts. Netdata was rejected for its RAM (100–150 MB), and a custom page
  was rejected as code to maintain.
- **Served at `/monitor/` on the same domain**, so no DNS change is needed.
  Caddy strips the prefix, and the hub builds its links from `APP_URL`. The
  hub publishes no port.
- **Opt-in with the compose profile `monitor`.** The first admin account is
  created at first boot from `BESZEL_USER_EMAIL` / `BESZEL_USER_PASSWORD` in
  `.env`. A hub with no users lets the first visitor create the admin
  account, so it must never be exposed without these.
- **The agent uses a Unix socket shared with the hub** (SSH mode). It needs
  only the hub's public key and no token. It runs with host networking and
  the Docker socket mounted read-only.
- **Files: `lifeos-metrics.sh` on a 1-minute systemd timer.** It writes daily
  CSVs to `/var/log/lifeos-metrics` (host and per container) and keeps 30 days.
  sysstat keeps collecting on its own.
- Both images are pinned by tag and digest, as Caddy is.

## Consequences

- **The Docker socket gives the agent root-equivalent access** to the VM,
  even read-only. That is trust in a third-party image, limited by the pinned
  digest.
- **The Beszel login is a second credential on the internet,** next to the
  API token. Its strength depends on the password the operator chooses.
- The Beszel data (metric history, users) lives in the `beszel-data` volume.
  It is lost with the VM unless backed up. The CSVs are the durable record.
- With the profile off, `/monitor/` answers 502. The API and the web app are
  unaffected.
