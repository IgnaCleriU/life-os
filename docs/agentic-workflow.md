# Life OS — Agentic Development Workflow

**Depends on:** [vision.md](vision.md), [roadmap.md](roadmap.md), [../ARCHITECTURE.md](../ARCHITECTURE.md)
**Scope of this document:** defines how an AI agent (e.g. Claude Code) should organize work on
this repo — from receiving a task to leaving it ready for review. It is prescriptive: it describes
the process the agent is expected to follow, not just a reference.

For commit conventions and the Pull Request workflow, see [../CONTRIBUTING.md](../CONTRIBUTING.md).

---

## 1. Roles

Development is organized around an **orchestrator model** that can delegate to **subagents**.

| Role | Responsibility |
|---|---|
| **Orchestrator** | Understands the task, decides the strategy, launches subagents, integrates their results, commits atomically, and opens the PR. It does not write the entire implementation itself: it coordinates. |
| **Research subagent** | Explores the repo (existing patterns, affected files, reusable utilities) and returns conclusions, not changes. Read-only. |
| **Implementation subagent** | Receives a bounded slice of work (a layer, a module, a file) and produces the changes for that slice. |

The orchestrator is solely responsible for the final state: even when it delegates, it reviews and
integrates everything before considering the task done.

---

## 2. Work cycle

```
┌──────────────────────────────────────────────────────────────────────┐
│ 1. Understand → 2. Investigate → 3. Plan → 4. Implement → 5. Integrate │
│                    (∥ subagents)   (if needed)  (∥ or serial)  and verify │
└──────────────────────────────────────────────────────────────────────┘
```

### 1. Understand the task
The orchestrator restates the goal and scope in its own words: what is being asked, what is out of
scope, and what "done" means. If there is a design ambiguity that affects the outcome, it asks
before proceeding.

### 2. Investigate
Before designing, the orchestrator launches **research subagents** to map the repo: existing
patterns, affected files, reusable utilities and use cases. When the areas to investigate are
independent (e.g. "how is the domain structured" vs. "how are use cases tested"), they are launched
**in parallel**. The rule is to reuse what already exists before proposing new code.

### 3. Plan
The orchestrator builds a plan **unless the task is very small**. Threshold:

- **No plan** — a trivial, bounded change: a single file, no design ambiguity, no effect on other
  layers (e.g. fixing a typo, adjusting a message, renaming a local variable).
- **Plan required** — everything else: any task touching more than one file or layer, adding
  behavior, or involving design decisions. The plan describes the steps, the files to touch, and
  how it will be verified.

When in doubt, make a plan.

### 4. Implement
The orchestrator splits the work across **implementation subagents**, deciding the mode based on
the dependencies between changes (see section 3):

- **In parallel** when the slices do not overlap (different layers or modules, no mutual
  dependency).
- **In serial** when one slice depends on another (what one produces must exist before the next
  one starts).

### 5. Integrate and verify
The orchestrator merges the subagents' results, resolves conflicts, runs tests and lint, and
confirms the definition of "done" is met. Only then does it commit (atomically, see
[../CONTRIBUTING.md](../CONTRIBUTING.md)) and open the PR.

---

## 3. When to parallelize vs. serialize

The project's [hexagonal architecture](../ARCHITECTURE.md) defines a dependency rule that serves as
a direct guide: **arrows point inward** (`adapters → application → domain`, and
`infrastructure → application`). Work is serialized along that direction and parallelized across
independent branches of work.

| Situation | Mode | Example |
|---|---|---|
| One slice uses a contract/entity that another must create first | **Serial** | Define the `TaskRepository` port **before** implementing `SQLiteTaskRepository`; define the `Task` entity **before** the `CompleteTask` use case |
| Slices in layers or modules with no mutual dependency | **Parallel** | Writing the REST adapter and the MCP adapter for an existing use case; working on the `projects` module and the `tasks` module when they share no changes |
| Investigating different areas of the repo | **Parallel** | One subagent maps the domain while another reviews testing patterns |
| Tests for a layer that was just implemented | **Serial** (after that layer) | Use-case tests once the use cases and their fake repository exist |

Rule of thumb: if the output of A is the input of B, they go in serial (A → B). If A and B can fail
or change without affecting each other, they go in parallel.

---

## 4. Workflow diagram

```
                      ┌─────────────────────────────┐
      task  ─────────►│         ORCHESTRATOR         │
                      │  understands · coordinates · integrates │
                      └───┬───────────┬───────────┬──┘
                          │           │           │
              investigation (∥)     plan     implementation
                  ┌───────┼───────┐   │      ┌──────┼──────┐
                  ▼       ▼       ▼   ▼      ▼      ▼      ▼
               [sub]   [sub]   [sub] (plan) [sub]  [sub]  [sub]
               domain  tests  patterns      domain→port  adapters
                                            (serial)        (∥)
                          │           │           │
                          └───────────┴───────────┴──► integrate + verify
                                                             │
                                                             ▼
                                              branch · atomic commits · PR to master
```

---

## 5. Parallel agents: isolation with git worktrees

When **several agents run at once on the same machine**, each must work on its own branch without
stepping on the others. A git repository has a single working tree and a single index, so two agents
in the same directory mix up each other's changes and branches.

The solution is **one git worktree per agent**: each gets its own working directory with its own
branch checked out, all backed by the same `.git`. In Claude Code this is enabled with the
**worktree** option (per-worktree isolation) when launching agents in parallel.

Benefits:

- Each agent commits on its branch (`<type>/<short-description>`) without affecting the others.
- Git refuses to check out the same branch in two worktrees → a guardrail against collisions.

> **Branch name.** The worktree may be created with an auto-generated name
> (e.g. `claude/busy-pare-e5448c`). Before integrating, rename the branch to
> a `<type>/<short-description>` coherent with the task — the auto-generated
> name must not reach the PR. See
> [../CONTRIBUTING.md](../CONTRIBUTING.md#branch-name).

Since they share the same `.git`, keep in mind:

- **`pre-commit`** is installed once (hooks live in the shared git-dir) and validates across all
  worktrees.
- **`backend/` Python environment**: each worktree is a new directory; if the venv lives inside the
  worktree, dependencies must be installed per worktree.
- **Dev ports and DB**: two agents starting the app or the SQLite DB at the same time collide (port
  8000, DB file). Running the app in parallel requires distinct ports/DBs.
- **Integration into `master`** is still sequential via PRs; worktrees avoid collisions during
  development, not at merge time.

---

## 6. Relation to PRs and commits

The agentic workflow ends in a delivery that follows the conventions in
[../CONTRIBUTING.md](../CONTRIBUTING.md):

- **One task = one branch = one PR** against `master`.
- The orchestrator turns the subagents' work into **several atomic commits** (one per coherent
  logical change), not a single giant commit, so the PR reads as a clear history.
- Messages follow [Conventional Commits](../CONTRIBUTING.md#commit-convention) and are validated
  locally with `pre-commit`.

---

*Living document — update as the way of working with agents evolves.*
