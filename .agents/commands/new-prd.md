# /new-prd — Create a Product Requirements Document

## Purpose

Guide the creation of a PRD for a new feature. This is the **mandatory first step** of the PRD → TDD → SDD workflow. No code changes without a prior approved PRD for substantial features.

PRDs are saved to `.agents/dev/prd-{feature-name}.md`.

---

## Rules (non-negotiable)

- Use `AskUserQuestion` for EVERY section — NEVER write assumptions without asking
- STOP after each section and wait for the answer before continuing to the next
- Each section MUST include a **Requirements** block with numbered requirements: `R-{PREFIX}-NN`
- Requirements must be written in imperative mood: "The system MUST...", "The API MUST...", "The module SHOULD..."
- Use `MUST` for mandatory, `SHOULD` for recommended, `MAY` for optional
- After all sections are complete, write the PRD file. Do NOT write it before finishing all sections.
- Do NOT start implementing. Do NOT suggest code. The PRD is a planning artifact only.

---

## Step 0 — Feature Name

Ask the user:
> "What's the feature name? (will be used as filename: `prd-{name}.md`)"

Use a short, kebab-case slug. Example: `gym-workout-sessions`, `macro-barcode-scanner`, `calendar-recurring-events`.

---

## Step 1 — Problem Statement (`R-PROB-NN`)

Ask:
> "What problem does this feature solve? What's missing or broken today without it?"

From the answer, derive requirements like:
- `R-PROB-01: The system MUST solve [X]`
- `R-PROB-02: The module MUST NOT require [workaround Y] to achieve [goal]`

Write the section as:
- A clear description of the problem (2–5 sentences)
- What happens currently without this feature
- Why it matters

**Requirements block** (generate from user's answer — minimum 2, maximum 6):
```
**Requirements:**
- R-PROB-01: ...
- R-PROB-02: ...
```

---

## Step 2 — Vision (`R-VIS-NN`)

Ask:
> "What should be true after this feature is implemented? Describe the before/after."

Write the section as a "before" and "after" contrast. One paragraph each.

**Requirements block** (minimum 1):
```
**Requirements:**
- R-VIS-01: The feature MUST deliver [measurable outcome]
```

---

## Step 3 — API Consumers & Stakeholders (`R-CON-NN`)

Ask:
> "Who calls these endpoints? (frontend, admin panel, scheduler/cron, another module, external service, etc.)"

Write a table:

| Consumer | How They Use It | Priority |
|----------|----------------|----------|
| Frontend | ... | P0 |
| Scheduler | ... | P1 |

**Requirements block** (minimum 2):
```
**Requirements:**
- R-CON-01: The API MUST be usable by [consumer] without [dependency]
- R-CON-02: Authentication MUST be required for all endpoints used by [consumer]
```

---

## Step 4 — Environment Requirements (`R-ENV-NN`)

Ask:
> "Any special environment requirements? (Python version, env vars, Docker config, DB schema that must already exist, etc.) Or is the standard setup enough?"

Write what's needed beyond the standard project setup. If nothing special, write "Standard project environment — no additional requirements."

**Requirements block** (minimum 1):
```
**Requirements:**
- R-ENV-01: The module MUST run within the existing Docker `api` service without changes to the base image
- R-ENV-02: [Any env var] MUST be defined in `.env.example`
```

---

## Step 5 — Dependencies & External Services (`R-DEP-NN`)

Ask:
> "What must already exist for this feature to work? (other modules, DB tables, external APIs, cron jobs, etc.)"

Write a dependency matrix:

| Dependency | Type | Why Needed | Status |
|-----------|------|-----------|--------|
| `gym_tracker` module | Internal module | Uses workout sessions | Already exists |
| `users` table | DB table | Foreign key for ownership | Already exists |
| External barcode API | External HTTP | ... | Must be configured |

**Requirements block** (minimum 2):
```
**Requirements:**
- R-DEP-01: [Module/table] MUST exist and be migrated before this feature can be deployed
- R-DEP-02: The feature MUST NOT create circular dependencies with [module]
```

---

## Step 6 — Features & Scope (`R-FEAT-NN`)

Ask:
> "List the main sub-features or capabilities to implement. What's explicitly OUT of scope?"

Write two subsections:

### In Scope
List each sub-feature with a brief description.

### Out of Scope
List explicitly what will NOT be built (prevents scope creep).

**Requirements block** (minimum 4 — one per major sub-feature):
```
**Requirements:**
- R-FEAT-01: The module MUST implement [sub-feature A]
- R-FEAT-02: The module MUST support [sub-feature B]
- R-FEAT-03: The module SHOULD support [optional sub-feature C]
- R-FEAT-04: The module MUST NOT implement [explicitly excluded item] in this version
```

---

## Step 7 — API Contract (`R-API-NN`)

Ask:
> "List the endpoints this feature exposes: method, path, and what it does. Include auth requirements per endpoint."

Write an endpoints table:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/{module}/` | Required | List all items |
| POST | `/api/v1/{module}/` | Required | Create a new item |
| GET | `/api/v1/{module}/{id}` | Required | Get item by ID |
| PATCH | `/api/v1/{module}/{id}` | Required | Update item |
| DELETE | `/api/v1/{module}/{id}` | Required | Delete item |

Then ask:
> "Any key request/response fields worth documenting? (IDs, required fields, enums, etc.)"

Write a brief schema for each key endpoint.

**Requirements block** (minimum 3):
```
**Requirements:**
- R-API-01: All endpoints MUST require JWT authentication via the existing auth middleware
- R-API-02: The API MUST return 404 when a resource does not exist or does not belong to the authenticated user
- R-API-03: POST and PATCH requests MUST validate input with Pydantic v2 schemas
- R-API-04: Responses MUST follow the existing project response format
```

---

## Step 8 — Technical Architecture (`R-ARCH-NN`)

Ask:
> "Any specific architectural decisions for this module? (special patterns, caching, background tasks, etc.) Or standard layered architecture?"

Write the module's layer structure following the project pattern:

```
Router (app/modules/{name}/router.py)
  └── Service (app/modules/{name}/service.py)
        └── SQLAlchemy Models (app/modules/{name}/models.py)
              └── PostgreSQL schema: {schema_name}
```

Describe any non-standard flows (webhooks, scheduled tasks, external calls, etc.).

**Requirements block** (minimum 2):
```
**Requirements:**
- R-ARCH-01: The module MUST follow the project's router → service → model layered pattern
- R-ARCH-02: Business logic MUST reside in the service layer, not in routers or models
- R-ARCH-03: [Any special architectural requirement]
```

---

## Step 9 — Migrations & Data Model (`R-DB-NN`)

Ask:
> "What new tables, columns, or relationships does this feature require? What's the Alembic migration strategy?"

Write the data model:

**New Tables:**

| Table | Schema | Description |
|-------|--------|-------------|
| `{table_name}` | `{schema}` | ... |

**Key Columns** (for each table):

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `user_id` | UUID | No | FK to users |
| `created_at` | TIMESTAMP | No | Auto-set |

**Relationships:** describe FK constraints and cascade rules.

**Requirements block** (minimum 3):
```
**Requirements:**
- R-DB-01: All new tables MUST be created in the `{schema}` PostgreSQL schema
- R-DB-02: All tables MUST include `id` (UUID PK), `created_at`, `updated_at` columns
- R-DB-03: The Alembic migration MUST be reversible (downgrade path required)
- R-DB-04: Foreign keys to `users` MUST use the pattern established in existing modules
```

---

## Step 10 — Acceptance Criteria (`R-ACC-NN`)

Ask:
> "What must be true for this feature to be considered complete? List the conditions — these will become the TDD test cases."

Write a checklist. Each item is a verifiable condition:

```
- [ ] All endpoints return correct status codes (200, 201, 400, 401, 404)
- [ ] Items are isolated per user (user A cannot access user B's data)
- [ ] Pagination works on list endpoints
- [ ] Soft delete / hard delete works as expected
- [ ] DB migrations run cleanly (upgrade + downgrade)
- [ ] All module tests pass
```

**Requirements block** (minimum 4 — these directly map to test cases):
```
**Requirements:**
- R-ACC-01: ALL acceptance criteria items MUST have corresponding pytest test cases
- R-ACC-02: The module MUST achieve 100% coverage of its service layer logic
- R-ACC-03: [Specific acceptance condition]
- R-ACC-04: [Specific acceptance condition]
```

---

## Step 11 — Non-Functional Requirements (`R-NFR-NN`)

Ask:
> "Any non-functional requirements? (performance SLAs, rate limits, security constraints, pagination limits, etc.) Or standard project defaults?"

Write subsections for:
- **Security**: auth requirements, data isolation, sensitive fields
- **Performance**: response time targets, pagination, max page size
- **Reliability**: idempotency requirements, error handling expectations

**Requirements block** (minimum 3):
```
**Requirements:**
- R-NFR-01: All write endpoints MUST be idempotent or clearly documented as non-idempotent
- R-NFR-02: List endpoints MUST support pagination with a maximum page size of [N]
- R-NFR-03: The module MUST NOT expose data belonging to other users under any circumstances
- R-NFR-04: [Performance or security requirement]
```

---

## Step 12 — Relationship to Other Modules (`R-REL-NN`)

Ask:
> "How does this module interact with other modules? (reads data from, writes to, triggers automations in, etc.)"

Write a table:

| Module | Relationship | Direction |
|--------|-------------|-----------|
| `automations_engine` | This module emits events that trigger automations | → outbound |
| `expenses_tracker` | Reads category data from expenses | ← inbound |
| `auth/user` | All items belong to a user (FK) | ← inbound |

**Requirements block** (minimum 2):
```
**Requirements:**
- R-REL-01: The module MUST NOT import directly from other modules — use shared models or events
- R-REL-02: Integration with `automations_engine` MUST follow the automation contract spec
```

---

## Step 13 — Future Considerations

Ask:
> "What's explicitly out of scope for this version but might be relevant later?"

Write a numbered list. These are NOT requirements — they're notes to inform future decisions without polluting the current implementation.

No requirements block for this section. These are deliberate deferrals, not actionable now.

---

## Step 14 — Success Metrics (`R-MET-NN`)

Ask:
> "How do we know this feature worked? What can we measure?"

Write a table:

| Metric | Target | How to Measure |
|--------|--------|---------------|
| All tests pass | 100% | `pytest app/modules/{name}/tests` |
| API response time | < 200ms p95 | Load test / manual check |
| Zero regressions | 0 failures | Full suite `pytest` |

**Requirements block** (minimum 2):
```
**Requirements:**
- R-MET-01: The full test suite MUST pass after this module is merged
- R-MET-02: Module-specific tests MUST achieve [X]% coverage
```

---

## Step 15 — Open Questions

Ask:
> "Any unresolved questions that need answers before or during implementation?"

Write a numbered list. Mark each with `[ ]` if unresolved or `[x]` if resolved.

```
1. [ ] Should items be soft-deleted or hard-deleted?
2. [ ] Does pagination use cursor-based or offset-based strategy?
3. [x] Auth: JWT required on all endpoints — confirmed.
```

No requirements block for this section.

---

## Final Step — Write the PRD File

After completing all 15 sections:

1. Assemble the full PRD using this header:

```markdown
# PRD: {Feature Name}

> {One-line tagline describing what this feature does}

**Version**: 0.1.0-draft
**Date**: {today YYYY-MM-DD}
**Status**: Draft
**Module**: `{module_name}`

---
```

2. Write all 15 sections in order with their requirements blocks.

3. Save to `.agents/dev/prd-{feature-name}.md`.

4. Confirm to the user:
   > "PRD written to `.agents/dev/prd-{feature-name}.md`. Review it, make any adjustments, then run `/new-tdd` to derive the test cases from the acceptance criteria."

5. STOP. Do not write any code. Do not start TDD. Do not start SDD.
