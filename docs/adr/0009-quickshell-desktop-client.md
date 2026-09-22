# 0009. Quickshell desktop client over a local REST daemon

- Status: Accepted
- Date: 2026-09
- Supersedes: [0005-deployment-target.md](0005-deployment-target.md)
- Amends: [0008-keyboard-driven-tui-adapter.md](0008-keyboard-driven-tui-adapter.md) (which client is primary, and how it reaches the use cases)
- Spec: [specs/0002-quickshell-desktop-client.md](../specs/0002-quickshell-desktop-client.md)

## Context

ADR 0008 made the Textual TUI the reference client, calling the use cases
in process. It works, but inside a terminal it is visually limited: no
blur, no mouse-driven drag and drop, no notifications, no live preview,
and it has to open a terminal window just to show a board. Life OS targets
one user on Omarchy (Hyprland). On Hyprland,
[Quickshell](https://quickshell.org) (QtQuick/QML) can draw layer-shell
overlays, bars and popups that sit on the desktop itself and follow the
active theme. A browser prototype of the board as a Quickshell overlay,
with the TUI's panes, modes and keymap, was reviewed and approved.

QML cannot import Python, so a Quickshell client cannot call the use cases
in process the way the TUI does. It needs a transport. ADR 0005 was also
deprecated without a replacement, which left open how the backend runs on
the desktop and what auth it needs (the Phase 0 "users, JWT" item).

## Decision

Make a **Quickshell client the primary human interface**. It lives in
`desktop/quickshell/`, outside the Python package. It reaches the
application layer **only through the existing REST adapter**, served by a
**long-running local daemon**. It has no business logic of its own,
exactly as in ADR 0002.

- **Runtime:** the REST adapter runs as a `systemd --user` service bound
  to `127.0.0.1` only. The Quickshell config runs as its own instance
  (`qs -c lifeos`), and Hyprland binds toggle it over Quickshell IPC.
  This is the desktop-app shape that replaces ADR 0005: everything runs
  locally, with nothing hosted and no remote access.
- **Auth:** there is one local user and no user accounts. Every request
  carries a random per-install token, read from a file with `0600`
  permissions, so other local users and web pages in a browser cannot
  drive the API. JWT and a user model are deferred until remote or
  multi-device access (Phase 6) is actually taken on.
- **Live updates:** the daemon exposes a cheap revision token that changes
  whenever *any* process (the daemon itself, MCP, CLI or TUI) commits to
  the shared database (ADR 0007). The client polls it and refetches on
  change.
- **Clients:** the TUI and CLI stay as in-process fallbacks for the
  terminal and SSH. The TUI is no longer the reference client. The rule
  that every capability is a use case first still holds. What changes is
  the bar: "reachable from the TUI" becomes "reachable over REST and
  exposed in the Quickshell client". MCP is unchanged.

## Consequences

- The board lives on the desktop: it opens as an overlay, gets mouse and
  drag-and-drop support, live quick-add parsing, notifications even while
  hidden, and it follows the Omarchy theme.
- A background process is now required for the primary UI. If the daemon
  is down, the client has to show that clearly. The TUI, CLI and MCP keep
  working without it.
- The REST API becomes a product surface rather than a spare adapter.
  Gaps it had only because nobody used it (quick-add, a revision
  endpoint) must be closed. Quick-add parsing and `#project` resolution
  stay in Python (`adapters/shared/`) and are exposed over REST, so they
  are not re-implemented in JavaScript.
- Agent writes over MCP show up in the UI within about a second, with no
  schema change. *Who* made a change (agent vs. human) is not recorded,
  so attribution waits for migrations (ADR 0003) and audit logging
  (Phase 7).
- The keymap now has two implementations (Python for the TUI, JS for
  Quickshell). The keymap table in spec 0001 remains the single source
  of truth, and each registry is tested against it.
- A second toolchain (QML/Qt) enters the repo. It can't run in CI without
  a Wayland session, so testable logic is kept in plain `.js` libraries,
  and the visual check stays manual.
- The Phase 0 auth item is resolved for the local case (a token, no
  accounts). ADR 0006's JWT choice stays dormant rather than deleted.

## Alternatives considered

- **Keep the TUI as the primary UI:** the cheapest option, but it keeps
  the limits that prompted this ADR.
- **Quickshell shelling out to `lifeos --json`:** no daemon and no backend
  changes, but it starts a Python process on every action and has no
  live updates. Fine for a prototype, too slow for the main UI.
- **Unix socket instead of TCP:** better isolation, but QML's
  `XMLHttpRequest` can't reach it without a native plugin. The token plus
  the loopback-only bind covers the same threat for a single-user machine.
- **A web frontend or Electron app:** it needs the same daemon, but it
  doesn't live on the desktop the way a layer-shell overlay does, and it
  adds a heavier runtime.
- **Server-sent events or WebSocket for live updates:** lower latency, but
  it needs streaming support in QML's JS engine that we haven't verified.
  Polling a revision token is enough at one user's scale and can be
  replaced later without an API break.
