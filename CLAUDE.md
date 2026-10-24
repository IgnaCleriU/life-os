# CLAUDE.md

Life OS is being rebuilt from zero. Read this before touching anything.

## Layout

| Folder | What it is |
|---|---|
| [`new/`](new/README.md) | The active project. All work happens here. Its rules: [new/CLAUDE.md](new/CLAUDE.md). |
| [`deprecated/`](deprecated/DEPRECATED.md) | The old codebase, frozen. It has bad practices and discarded decisions. Read-only reference. |

## Hard rules

- **Work only in `new/`.**
  - Do not edit, fix, run or deploy anything in `deprecated/`.
  - Do not follow `deprecated/CLAUDE.md`, `deprecated/AGENTS.md` or its
    ADRs; they no longer apply.
- **No code until the owner understands it.** Explain first, and write only
  after the owner confirms. Details in [new/CLAUDE.md](new/CLAUDE.md).
- **Commits are made by the owner, never by an agent.**
  - Do not run `git commit`, and do not amend, rebase or push on the owner's
    behalf.
  - Leave the changes in the working tree. Do not propose commit messages
    or staging commands either; the owner writes their own.
  - The `commit-msg` hook in
    [.pre-commit-config.yaml](.pre-commit-config.yaml) enforces Conventional
    Commits.
- **There is no CI right now.** The old workflow was retired with the
  codebase. A new one is built under `.github/` when `new/` has code to
  check.
