# CLAUDE.md

Life OS is being rebuilt from zero. Read this before touching anything.

## Layout

| Folder | What it is |
|---|---|
| [`new/`](new/README.md) | The active project. All work happens here. Its rules: [new/CLAUDE.md](new/CLAUDE.md). |
| [`aprendizaje/`](aprendizaje/README.md) | The owner's study notes, in Spanish: design patterns and Java topics, each tied back to `new/`. |
| [`deprecated/`](deprecated/DEPRECATED.md) | The old codebase, frozen. It has bad practices and discarded decisions. Read-only reference. |

## Hard rules

- **Work only in `new/`,** plus the study notes in `aprendizaje/`.
  - Do not edit, fix, run or deploy anything in `deprecated/`.
  - Do not follow `deprecated/CLAUDE.md`, `deprecated/AGENTS.md` or its
    ADRs; they no longer apply.
- **Document what you teach.** When you explain a concept to the owner (a
  design pattern, a Java feature), also write it up in
  [`aprendizaje/`](aprendizaje/README.md), in Spanish:
  - patterns go in `patrones-de-diseno/`, Java topics in `java/`;
  - add each new note to the index in `aprendizaje/README.md`;
  - each note covers the concept in general and then how it applies in
    `new/`, with a link.
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
- **Every commit is authored by IgnaCleriU, with no AI co-authorship.**
  - No `Co-authored-by` trailers and no "Generated with Claude Code" lines,
    in commits or in pull request titles and bodies. A PR body becomes the
    squash commit body on `master`.
  - The `pr-rules` check
    ([.github/workflows/pr-rules.yml](.github/workflows/pr-rules.yml))
    rejects any PR that breaks this.
- **GitHub flow.**
  - `master` only changes through pull requests, which are squash-merged.
    The PR title is the commit title, so it must be a Conventional Commit.
  - The `master` ruleset has no bypass actors, admin included. Never
    disable or edit it to get a change through; ask the owner.
  - Stacked pull requests (GitHub native stacks, `gh stack`) are welcome
    for work that splits into dependent steps.
- **CI.** For now the only check is `pr-rules`. Build and test jobs for
  `new/` are added under `.github/workflows/` once it has code to check.
