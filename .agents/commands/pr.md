---
allowed-tools: Bash(git log:*), Bash(git diff:*), Bash(git push:*), Bash(git checkout:*), Bash(git branch:*), Bash(git pull:*), Bash(gh pr create:*), Bash(gh pr merge:*), Bash(gh pr view:*), Bash(gh issue:*)
description: Create a pull request from current branch to develop
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
- Branch name MUST match: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$`

**Steps:**
1. Verify branch name matches the required pattern
2. Run tests before creating the PR: `docker-compose exec api pytest` — if they fail, STOP and warn the user. Skip tests if changes are documentation-only.
3. Push branch to remote: `git push -u origin HEAD`
4. Draft the PR title and body using the template below. **Show the full draft to the user and STOP — wait for explicit confirmation before creating the PR.**
5. Once confirmed, create the PR with `gh pr create --base develop`
6. Show the PR URL and STOP — wait for user confirmation before proceeding to merge

---

**PR title format:** `<type>(<scope>): <short imperative description>` — max 70 chars

Examples:
- `fix(automations): audit and fix 9 bugs in engine and calendar contract`
- `feat(gym_tracker): add automation contract with 5 triggers and 4 actions`

---

**PR body template** (follows `.github/PULL_REQUEST_TEMPLATE.md`):

```markdown
## 🔗 Linked Issue

<!-- Solo developer — create a tracking issue if one doesn't exist, or note N/A -->
Closes #

---

## 🏷️ PR Type

- [ ] `type:bug` — Bug fix
- [ ] `type:feature` — New feature
- [ ] `type:docs` — Documentation only
- [ ] `type:refactor` — Code refactoring (no behavior change)
- [ ] `type:chore` — Maintenance, dependencies, tooling
- [ ] `type:breaking-change` — Breaking change

---

## 📝 Summary

-

## 📂 Changes

| File | Change |
|------|--------|
| `path/to/file` | What changed |

## 🧪 Test Plan

- [ ] Tests pass locally: `docker-compose exec api pytest`
- [ ] Module tests pass: `docker-compose exec api pytest app/modules/<mod>/tests -v`
- [ ] Manually tested the affected functionality

---

## ✅ Contributor Checklist

- [ ] Linked issue above (`Closes #N`)
- [ ] Added exactly one `type:*` label to this PR
- [ ] Tests pass locally
- [ ] Docs updated if behavior changed (`/update-docs`)
- [ ] Commits follow conventional commits format
- [ ] No `Co-Authored-By` trailers in commits

---

## 💬 Notes for Reviewers

```

Add the corresponding `type:*` label to the PR after creation using `gh pr edit <number> --add-label "type:feature"`.

---

## After the PR is merged

Only proceed **after the user explicitly confirms** the PR is approved and CI passed:

1. Merge to develop: `gh pr merge <number> --merge`
2. Switch to develop: `git checkout develop`
3. Delete local branch: `git branch -d <branch>`
4. Delete remote branch: `git push origin --delete <branch>`
5. Pull latest: `git pull`
