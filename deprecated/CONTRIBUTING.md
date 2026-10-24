> [!CAUTION]
> **DEPRECATED. DO NOT USE THIS FILE AS A GUIDE.**
> This is the old Life OS codebase, frozen on 2026-10-24. It was built
> with known bad practices: a Java backend written as a partial clone of the
> Python one, two implementations sharing one database, and decisions
> (ADRs included) that grew out of early design errors. Nothing here is a
> requirement or a constraint for new work, and its rules do not apply.
> Read it only to look up a pattern, never to copy a decision.
> Active development lives in [`new/`](../new/README.md). Details in
> [`deprecated/DEPRECATED.md`](./DEPRECATED.md).

# Contributing

This document defines the conventions for working on Life OS. It applies
both to human contributions and to AI agents (e.g. Claude Code) operating
on the repository.

## Commit convention

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>)<!>: <description in imperative mood, lowercase, no trailing period>
```

### Types

| Type | When to use it |
|---|---|
| `feat` | New functionality visible to the user or the agent (new endpoint, new MCP tool, new screen) |
| `fix` | Bug fix |
| `docs` | Documentation-only changes (`docs/`, `README`, `CONTRIBUTING.md`, architecture comments) |
| `refactor` | Code change that does not alter external behavior, add a feature, or fix a bug |
| `test` | Add or fix tests, without touching production code |
| `chore` | Maintenance tasks that don't fit the other types (dependencies, tooling configuration, file cleanup) |
| `build` | Changes affecting the build system or external dependencies (Dockerfile, docker-compose.yml, pyproject.toml) |
| `ci` | Changes to continuous integration configuration |
| `style` | Formatting/style changes that don't affect logic (whitespace, automatic formatting) |
| `perf` | Changes that improve performance |
| `revert` | Revert a previous commit |

### Scopes

Free-form and optional — there is no closed list yet. Use them organically
to indicate the layer (`domain`, `application`, `infrastructure`,
`adapters-rest`, `adapters-mcp`), the module (`projects`, `tasks`), or the
client (`frontend`, `cli`, `android`) affected.

### Examples

```
feat(tasks): add complete task endpoint
fix(mcp): fix project_id validation in create_task
docs: define commit convention and add pre-commit hook
refactor(domain): extract Task status validation
chore: update fastapi dependency
```

### Breaking changes

Changes that break contracts between layers (e.g. a signature change in a
port/`Protocol`) or public API contracts are marked with `!` after the
type/scope, or with a `BREAKING CHANGE:` footer explaining the impact:

```
feat(application)!: change signature of TaskRepository.list_by_project
```

## Atomic commits

A task is not resolved with a single giant commit: it is split into
**several atomic commits** so the Pull Request reads as a clear story and
is easy to review.

Rules:

- **One commit = one complete, coherent logical change**, which ideally
  compiles and passes tests on its own.
- **Do not mix** feature + refactor + fix in the same commit. Each commit
  uses the `type` that corresponds to it.
- Order commits following the architecture's
  [dependency rule](ARCHITECTURE.md) (inside out): domain → ports → use
  cases → infrastructure → adapters → tests.

### Example: a task split into atomic commits

Task: "add the ability to complete a Task."

```
feat(domain): add done state transition to Task
feat(application): add TaskRepository port
feat(application): add CompleteTask use case
feat(infrastructure): implement SQLiteTaskRepository
feat(adapters-rest): add POST /tasks/{id}/complete endpoint
feat(adapters-mcp): add complete_task tool
test(application): test the CompleteTask use case
```

Each line is reviewable in isolation, and the sequence tells the story of
what was done and in what order.

## Automatic validation (pre-commit)

The commit message format is automatically validated with
[`pre-commit`](https://pre-commit.com) and the
[`conventional-pre-commit`](https://github.com/compilerla/conventional-pre-commit)
hook.

Installation (once per repo clone):

```
pip install pre-commit
pre-commit install --hook-type commit-msg
```

From that point on, any commit whose message does not follow the format
above is rejected locally before being created.

## Pull Request flow

Never commit directly to `master`. Every task is worked on its own
**branch** and integrated through a Pull Request.

1. **Start from an up-to-date `master`** and create a new branch for the task.
2. **Work on the branch**, leaving the task as [atomic commits](#atomic-commits).
3. **Open a PR against `master`** when done; the PR contains those commits.

### Branch name

Format `<type>/<short-description>` in kebab-case, using the same `<type>`
as the task's main commit (the types from the
[commit convention](#types)):

```
feat/complete-task
fix/project-id-validation
docs/agentic-workflow
refactor/extract-task-validation
```

**The name must describe the task.** Do not leave the branch with the
tool's auto-generated name (e.g. `claude/busy-pare-e5448c`): those names say
nothing about the work. Rename the branch to `<type>/<short-description>`
before opening the PR.

### PR contents

- **Title** in Conventional Commits style (same format as a commit), e.g.
  `feat(tasks): add complete task`.
- **Description** including: what was done, why, and how to verify it
  (tests to run, endpoint/tool to try).
- Commit messages are already validated locally by `pre-commit` (see
  previous section).

The agentic workflow that produces these PRs is described in
[docs/agentic-workflow.md](docs/agentic-workflow.md).
