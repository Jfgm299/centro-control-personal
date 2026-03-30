---
allowed-tools: Bash(docker-compose exec:*), Bash(git diff:*), Bash(git log:*)
description: Pre-deploy checklist — verify everything before merging to main
---

## Task

Run through this checklist point by point before merging to `main`. Do not skip any step.

## 1. Tests

```bash
docker-compose exec api pytest
```

All must pass. If there are failures, **do NOT proceed** — stop and report them.

## 2. Migrations

```bash
docker-compose exec api alembic upgrade head
docker-compose exec api alembic current
```

- Does `current` point to the expected head?
- Are there pending migrations for any model changes that were not generated?

## 3. Generate migration if there are model changes

```bash
docker-compose exec api alembic revision --autogenerate -m "<description>"
```

Review the generated file — confirm it only touches the expected tables.

## 4. Environment variables

- Are all new env vars added to `.env.example`?
- Are they configured in staging/prod?

## 5. Quick security review

- No new endpoint exposes another user's data (ownership checks in place)?
- No hardcoded credentials?
- Exception handlers cover the new error cases?

## 6. Automation contract changes

If the automation contract was modified:
- Was `automation_registry.py` updated in the affected module?
- Do new handlers follow the `(payload, config, db, user_id) -> dict` signature?
- Do triggers return `{"matched": bool, ...}` and actions return `{"done": bool, ...}`?

## 7. Documentation

- Do the docs in `.agents/docs/` reflect the changes?
- If you added a model, endpoint, module, or automation handler — run `/update-docs` first.
