---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git checkout:*), Bash(git branch:*)
description: Generate a conventional commit for staged changes (repo-scoped)
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Staged diff: !`git diff --staged`
- Recent commits (style reference): !`git log --oneline -5`

## Task

Generate and execute **atomic conventional commits** for the pending changes.

By default, do **not** create one giant commit when multiple concerns are mixed. Split into the minimum number of coherent commits so each commit is independently reviewable and reversible.

**Rules (non-negotiable):**

- Commit message MUST be in **English** — always, no exceptions
- Command scope MUST stay inside the current repository
- Never use `--no-verify`
- Never commit `.env` or files with credentials
- Never commit directly to `main` or `develop` — if on those branches, infer a branch name from the staged changes and create it automatically following the branch naming rules below, then proceed with the commit on the new branch
- If there are **multiple unrelated change groups**, create **multiple commits** (atomic commits)
- If all changes are clearly one concern, a single commit is acceptable
- If split is ambiguous, propose the commit plan first and ask for confirmation before committing

**Branch naming (enforced by GitHub ruleset — pushes that don't match will be rejected):**

Pattern: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$`

| Type       | When to use                     | Example                            |
| ---------- | ------------------------------- | ---------------------------------- |
| `feat`     | new functionality               | `feat/habit-tracker-module`        |
| `fix`      | bug fix                         | `fix/duplicate-observation-insert` |
| `chore`    | maintenance, deps, config       | `chore/bump-sqlalchemy-v2`         |
| `docs`     | documentation only              | `docs/automation-contract-update`  |
| `style`    | formatting, no logic change     | `style/fix-router-alignment`       |
| `refactor` | code change, no behavior change | `refactor/extract-query-sanitizer` |
| `perf`     | performance improvement         | `perf/optimize-fts5-queries`       |
| `test`     | adding or updating tests        | `test/add-gym-tracker-coverage`    |
| `build`    | build system changes            | `build/update-docker-compose`      |
| `ci`       | CI/CD changes                   | `ci/split-test-job`                |
| `revert`   | reverting a previous commit     | `revert/broken-migration`          |

Description rules: lowercase only, `a-z 0-9 . _ -` allowed, no spaces, no uppercase.

**Commit message format:** `<type>(<optional-scope>): <short description in imperative mood>`

Valid commit types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`

Examples:

- `feat(calendar): add routine exceptions support`
- `fix(automations): correct recursion depth check`
- `chore(deps): upgrade sqlalchemy to v2`
- `docs(gym_tracker): update automation contract section`

**Body (optional):** if the why is not obvious, add a blank line + short explanation.

## Atomic Commit Strategy (default)

1. Inspect unstaged + staged changes.
2. Group files by concern (feature area / bugfix / refactor / docs / tests).
3. Create one commit per concern:
   - stage only files for that concern
   - commit with a precise conventional message
4. Repeat until working tree is clean.

### Grouping heuristics

- Keep code changes separate from docs-only changes when possible.
- Keep refactors separate from behavior changes.
- Keep test-only changes separate unless they are tightly coupled to the same behavior change.
- Avoid mixing provider, config, and CLI concerns in one commit unless they represent one inseparable vertical slice.

### Output requirements

- Before committing, print the proposed commit plan:
  - commit N title
  - files included
  - rationale (1 line)
- After execution, print all created commit SHAs and titles in order.

### Override

- If the user explicitly asks for a single commit, follow that instruction.
