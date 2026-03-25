---
allowed-tools: Bash(git log:*), Bash(git diff:*), Bash(git push:*), Bash(git checkout:*), Bash(git branch:*), Bash(git pull:*), Bash(gh pr create:*), Bash(gh pr merge:*), Bash(gh pr view:*)
description: Crea un Pull Request de la rama actual -> develop (titulo y body en ingles)
---

## Context

- Current branch: !`git branch --show-current`
- Commits ahead of develop: !`git log develop..HEAD --oneline`
- Diff vs develop: !`git diff develop..HEAD --stat`
- Uncommitted changes: !`git status --short`

## Task

Create a Pull Request from the current branch into `develop`.

**Rules (non-negotiable):**
- PR title and body MUST be in **English** — always, no exceptions
- Never target `main` directly — PRs always go to `develop`
- If there are uncommitted changes, STOP and warn the user before proceeding
- If the branch name doesn't follow `feat/`, `fix/`, `chore/`, `refactor/` — warn the user

**Steps:**
1. Verify branch name is valid (`feat/`, `fix/`, `chore/`, `refactor/`)
2. Push branch to remote if not already there: `git push -u origin HEAD`
3. Create the PR with `gh pr create --base develop` using the template below
4. Show the PR URL and STOP — wait for user confirmation before doing anything else

**PR title format:** `<type>(<scope>): <short imperative description>` — max 70 chars
Examples:
- `fix(automations): audit and fix 9 bugs in engine and calendar contract`
- `feat(expenses): auto-convert overdue subscriptions`

**Body template:**
```
## What does this PR do?
<brief description>

## Main changes
-

## How to test
- docker-compose exec api pytest app/modules/<mod>/tests -v

## Notes
<migrations, breaking changes, dependencies — omit section if none>
```

---

## After the PR is merged

Only proceed with the following steps **after the user explicitly confirms** the PR is approved and CI passed:

1. Merge to develop: `gh pr merge <number> --merge`
2. Switch to develop: `git checkout develop`
3. Delete local branch: `git branch -d <branch>`
4. Delete remote branch: `git push origin --delete <branch>`
5. Pull latest: `git pull` — always, without exception, so the next branch starts from updated develop
