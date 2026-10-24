# Life OS

A personal operating system: projects and tasks first, and later notes,
calendar, passwords and home inventory, usable both by its owner and by AI
agents.

This folder is a **restart from zero**. The previous version lives in
[`../deprecated/`](../deprecated/DEPRECATED.md) and is not a base for this
one. Nothing here inherits its decisions, its ADRs, its schema or its data.

## Status

Empty. Each piece is added through a concrete, scoped job (see
[How we work](#how-we-work)), and this README is updated as the structure
appears.

## Stack

| | |
|---|---|
| Language | Java 21 (LTS) |
| Framework | Spring Boot, at the adapter edge only |
| Build | Maven, through the Maven Wrapper (`./mvnw`) |
| Tests | JUnit 5 + AssertJ, strict TDD |

The persistence engine is not chosen yet. It is decided in the job that
first needs it.

## Architecture

Hexagonal (ports and adapters), designed here from scratch:

- **The domain and the use cases are plain Java.** They know nothing about
  Spring, HTTP or the database.
- **Dependencies point inward:** adapters → application → domain.
  Infrastructure implements ports that the application defines.
- **The build enforces the boundaries wherever it can.** Whatever it cannot
  enforce is written down as an explicit rule, together with how it is
  checked.

The details are written down as each layer is built.

## How we work

The project doubles as a course: the owner learns the system by building
it.

- **Concrete jobs.** Each step is a small piece of work with a clear purpose
  and a clear "done" criterion.
- **Understand before code.** Every design is explained and agreed before
  any code is written.
- **Mixed authorship.**
  - The owner writes the core: the domain and the use cases.
  - Claude writes repetitive parts, such as build setup, configuration and
    boilerplate. It does so only after explaining them and only once the
    owner confirms they understand them.
- **Strict TDD.** Red, then green, then refactor, with every step visible.
- **Documentation.**
  - Markdown, written only where prose is actually needed.
  - Diagrams in PlantUML.
  - Interactive pages (artifacts) only on request.

The working rules for AI agents are in [CLAUDE.md](CLAUDE.md).
