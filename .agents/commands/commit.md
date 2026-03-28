---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*), Bash(git checkout:*), Bash(git branch:*)
description: Generate a conventional commit for staged changes
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Staged diff: !`git diff --staged`
- Recent commits (style reference): !`git log --oneline -5`

## Task

Generate and execute a single git commit for the staged changes above.

**Rules (non-negotiable):**
- Commit message MUST be in **English** — always, no exceptions
- Never use `--no-verify`
- Never commit `.env` or files with credentials
- Never commit directly to `main` or `develop` — if on those branches, infer a branch name from the staged changes and create it automatically following the branch naming rules below, then proceed with the commit on the new branch

**Branch naming (enforced by GitHub ruleset — pushes that don't match will be rejected):**

Pattern: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$`

| Type | When to use | Example |
|------|------------|---------|
| `feat` | new functionality | `feat/habit-tracker-module` |
| `fix` | bug fix | `fix/duplicate-observation-insert` |
| `chore` | maintenance, deps, config | `chore/bump-sqlalchemy-v2` |
| `docs` | documentation only | `docs/automation-contract-update` |
| `style` | formatting, no logic change | `style/fix-router-alignment` |
| `refactor` | code change, no behavior change | `refactor/extract-query-sanitizer` |
| `perf` | performance improvement | `perf/optimize-fts5-queries` |
| `test` | adding or updating tests | `test/add-gym-tracker-coverage` |
| `build` | build system changes | `build/update-docker-compose` |
| `ci` | CI/CD changes | `ci/split-test-job` |
| `revert` | reverting a previous commit | `revert/broken-migration` |

Description rules: lowercase only, `a-z 0-9 . _ -` allowed, no spaces, no uppercase.

**Commit message format:** `<type>(<optional-scope>): <short description in imperative mood>`

Valid commit types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`

Examples:
- `feat(calendar): add routine exceptions support`
- `fix(automations): correct recursion depth check`
- `chore(deps): upgrade sqlalchemy to v2`
- `docs(gym_tracker): update automation contract section`

**Body (optional):** if the why is not obvious, add a blank line + short explanation.

Stage any unstaged files that are relevant to the changes, then commit in a single step.
