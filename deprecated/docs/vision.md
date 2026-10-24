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

# Life OS — Product Vision

## Overview / Problem

Personal data is fragmented across notes apps, password managers, calendars,
task trackers, and spreadsheets, with no single source of truth and no
consistent way to act on it programmatically. Life OS is a personal
operating system that centralizes notes, passwords, calendar, projects and
tasks, and home inventory in one place, and exposes that data to AI agents
through a custom MCP (Model Context Protocol) server.

The goal is not just storage: it is to make personal data addressable and
actionable by an AI agent (for example Claude) in the same conversation
where the user is planning, deciding, or asking questions — without the
agent needing direct database access or a bespoke integration per client.

## Target user

Life OS is designed for a single user, self-hosted, personal use. It is not
a multi-tenant product and does not aim to support teams, organizations, or
shared accounts. The user is expected to run and own the full stack
(backend, database, MCP server) rather than depend on a third-party
provider.

## Core value proposition

An AI agent can read and modify the user's personal data — projects,
tasks, notes, calendar events, passwords, home inventory — through a
purpose-built MCP server, using the same business rules and validations as
every other client (web frontend, CLI, mobile app). This turns the agent
into a first-class client of the system rather than a workaround that
talks to files or screenshots.

## Data modules

Life OS is designed around six data domains. The MVP covers the first one;
the rest follow in later phases (see [roadmap.md](roadmap.md)):

1. **Projects & Tasks (MVP)** — projects, tasks, subtasks, status,
   priority, due dates, tags.
2. **Notes** — free-form text, markdown, links between notes (optional
   Zettelkasten-style structure), tags.
3. **Calendar** — events, reminders, recurrence, optional integration with
   external calendars (e.g. Google Calendar).
4. **Passwords / Vault** — the most sensitive module; see safety
   principles below and the ADR index for the storage approach.
5. **Home inventory** — items, categories, location, photos,
   warranties/expirations.
6. **Future modules** — personal finances, contacts, documents/files.

**Modeling recommendation.** Notes, Projects, and Home Inventory should
share a common "entity + tags + relations" model (similar to Notion or
Obsidian), so they can reuse the same UI components and generic endpoints
(search, tagging, attachments). Calendar and Passwords have their own
rules and constraints and should instead use dedicated, more rigid data
models rather than fit the generic entity model.

## Agent access model

The MCP server is the mechanism through which AI agents read and modify
Life OS data. It does not talk to the database directly — it consumes the
same use cases as the REST adapter (see
[../ARCHITECTURE.md](../ARCHITECTURE.md)), so every business rule applies
consistently regardless of which client originated the action.

**Suggested MVP tool surface** (as product capabilities, not an API spec):

- List, create, and update projects.
- List tasks within a project (optionally filtered by status), create
  tasks, update tasks, and mark tasks as complete.
- A generic cross-module search, useful from day one and intended to
  extend naturally as new modules (Notes, Calendar, ...) are added.

**Safety principles:**

- **Default-deny on Passwords.** No agent has access to the Passwords /
  Vault module by default; access must be explicitly granted.
- **Audit logging of agent writes.** Every write performed by an agent is
  logged with a timestamp and the originating tool, independent of the
  client-facing feature set.
- **Granular permissions.** What an agent can read or write is
  configurable per module, not all-or-nothing.

Decisions about the underlying stack, the password storage approach, and
deployment topology are tracked as Architecture Decision Records rather
than detailed here — see [adr/README.md](adr/README.md).

## Non-goals

- Multi-tenant or multi-user support (accounts, organizations, sharing).
- Reinventing password encryption from scratch as a default path; see the
  ADR index for the recommended approach.
- Being a general-purpose public product; Life OS is built for a single
  self-hosted user, not for external distribution.
- Replacing specialized tools (e.g. full accounting software) — the
  "future modules" (finances, contacts, documents) are lightweight
  personal trackers, not enterprise-grade systems.
