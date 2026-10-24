> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../../../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](../../DEPRECATED.md).

# Specs

A spec is a design/implementation document: the detailed design (UI, data
flow, syntax, keymaps) and the implementation steps to get there, for work
with enough surface area to be worth writing down. Not every task needs
one — a spec earns its place when there's real design content to capture,
not for its own sake.

Specs have **their own number sequence**, independent of
[../adr/](../adr/README.md). Most decisions don't need an ADR at all — an
ADR is only for structural or costly-to-reverse decisions (new domain
concepts, adapter boundaries, data model changes). A spec for, say, a TUI
color palette has no ADR and doesn't need one.

When a spec *does* elaborate a decision significant enough for an ADR, it
links back to it (see the template's optional `ADR:` line) and the ADR
links forward to the spec from its Status block — but the two numbers do
not need to match. This first spec is `0001` even though it elaborates ADR
`0008`, since the two sequences are independent.

The "Implementation tasks" table in a spec is the plan as written when it
was authored — it is not kept in sync afterward. Once work starts, the same
tasks are tracked live in the life-os task tracker via MCP; the table is
the plan, the tracker is the current status.

To propose a new spec, copy [0000-template.md](0000-template.md) and give
it the next free number.

## Index

| Number | Title | ADR |
|---|---|---|
| [0001](0001-keyboard-driven-tui-adapter.md) | Keyboard-driven TUI adapter | [adr/0008](../adr/0008-keyboard-driven-tui-adapter.md) |
| [0002](0002-quickshell-desktop-client.md) | Quickshell desktop client | [adr/0009](../adr/0009-quickshell-desktop-client.md) |
