# AI Agent Config Unification & PRD-TDD-SDD Workflow

## Part I: Current State & Problem Analysis

### 1. Executive Summary

This document defines a complete strategy for two interconnected goals:

1. **Config Unification** -- Eliminate duplication between Claude Code (`~/.claude/`) and OpenCode (`~/.config/opencode/`) configs, reducing the global `CLAUDE.md` from ~322 lines to ~30 lines per tool entry point, centralizing shared content in `~/.agents/`, and establishing a single source of truth at the project level.

2. **PRD-TDD-SDD Integrated Workflow** -- Define a structured pipeline where Product Requirements Documents (PRDs) drive Test-Driven Development (TDD) test suites, which then feed the existing Spec-Driven Development (SDD) workflow. This closes the gap between "what to build" and "how to verify it works."

Key metrics after migration:
- **Global entry points**: 322 lines -> ~30 lines each (Claude Code + OpenCode)
- **Config sources**: 2 divergent -> 1 canonical with thin wrappers
- **Duplication**: ~200 lines of persona/protocol duplicated -> 0
- **Command drift risk**: 4 duplicated commands -> 0 (wrappers reference canonical)
- **Skill directories**: 2 copies (16 + 11) -> 1 canonical with symlinks

---

### 2. Current State Audit

#### 2.1 Global Level

**Claude Code (`~/.claude/`)**

| File/Dir | Lines | Content |
|----------|-------|---------|
| `CLAUDE.md` | ~322 | Persona + Engram protocol + SDD orchestrator + rules + skills table + shared context ref |
| `settings.json` | 40 | Permissions (engram MCP allow, .env deny), model: opus, outputStyle, enabledPlugins, statusLine |
| `skills/` | 16 dirs | sdd-init/explore/propose/spec/design/tasks/apply/verify/archive, go-testing, skill-creator, create-issue, deploy-ios, status-cli-theme, frontend-ui-ux-engineer, _shared/ |
| `commands/` | N files | commit.md, pr.md, etc. |
| `shared/shared-context.md` | ~50 | Cross-repo project state |
| `mcp/` | configs | MCP server configurations (engram) |
| `plugins/` | data | Plugin system data |
| `projects/` | state | Per-project session state |

**OpenCode (`~/.config/opencode/`)**

| File/Dir | Lines | Content |
|----------|-------|---------|
| `AGENTS.md` | ~192 | Persona + SDD orchestrator (DUPLICATED from CLAUDE.md, subset) |
| `opencode.json` | 60 | 2 agents (gentleman, sdd-orchestrator), 2 MCPs (context7, engram), permissions |
| `skills/` | 11 dirs | Subset of Claude's skills (DUPLICATED) |
| `commands/` | 8 files | SDD commands (sdd-apply, sdd-archive, sdd-continue, sdd-explore, sdd-ff, sdd-init, sdd-new, sdd-verify) |
| `plugins/engram.ts` | TS | Engram integration plugin |

**Duplication Matrix -- Global:**

| Content Block | In CLAUDE.md | In AGENTS.md | Status |
|---------------|-------------|-------------|--------|
| Persona (personality, language, tone, philosophy, expertise, behavior) | Yes (~50 lines) | Yes (~50 lines) | DUPLICATED |
| Rules | Yes (~8 lines) | Yes (~8 lines) | DUPLICATED |
| Engram Protocol | Yes (~80 lines) | No | Claude-only |
| SDD Orchestrator | Yes (~120 lines) | Yes (~100 lines) | DUPLICATED with drift |
| Skills table | Yes (~10 lines) | Yes (~10 lines) | DUPLICATED |
| Shared context ref | Yes | No | Claude-only |

**Shared infrastructure (NOT duplicated):**
- Engram SQLite DB at `~/.local/share/engram/engram.db` -- both tools use same DB via MCP

#### 2.2 Project Level (centro-control)

**`.claude/` (complete)**

| File/Dir | Content |
|----------|---------|
| `CLAUDE.md` | 41 lines: stack, critical rules, conventions, @doc refs, quick reference |
| `commands/` | 6 commands: commit, pr, test, deploy-check, new-module, update-docs |
| `docs/` | 5 architecture docs + 8 module docs (13 files total) |
| `settings.local.json` | Project permissions (git, docker-compose) |

**`.opencode/` (thin)**

| File/Dir | Content |
|----------|---------|
| `commands/` | 4 commands: commit, pr, prompt, update-docs |
| `package.json` | @opencode-ai/plugin dependency |
| No AGENTS.md | No project-level agent instructions |
| No docs/ | No architecture documentation |

**Duplication Matrix -- Project:**

| Command | In .claude/ | In .opencode/ | Status |
|---------|------------|--------------|--------|
| `commit` | Yes | Yes | DUPLICATED -- drift risk |
| `pr` | Yes | Yes | DUPLICATED -- drift risk |
| `update-docs` | Yes | Yes | DUPLICATED -- drift risk |
| `test` | Yes | No | Claude-only |
| `deploy-check` | Yes | No | Claude-only |
| `new-module` | Yes | No | Claude-only |
| `prompt` | No | Yes | OpenCode-only |

#### 2.3 Syntax Incompatibilities

| Feature | Claude Code | OpenCode |
|---------|------------|----------|
| Lazy file references | `@docs/architecture.md` | `{file:./AGENTS.md}` |
| Permissions | `settings.json` -> `permissions.allow/deny` | `opencode.json` -> `permission.bash/read` |
| Agent definition | Implicit (single agent) | `opencode.json` -> `agent` block (multiple agents) |
| MCP config | `mcp/` directory or plugins | `opencode.json` -> `mcp` block |
| Skill loading | Built-in skill system + plugins | Manual file references |
| Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` |

#### 2.4 Cost of Duplication

1. **Drift risk**: When persona rules change in CLAUDE.md, AGENTS.md must be manually updated. Currently already out of sync (AGENTS.md has ~192 lines vs CLAUDE.md ~322 lines -- missing Engram protocol entirely).
2. **Maintenance overhead**: Every skill update requires copying to both `~/.claude/skills/` and `~/.config/opencode/skills/` (16 vs 11 dirs -- already 5 skills missing from OpenCode).
3. **Context waste**: 322 lines of CLAUDE.md loaded into every Claude Code session. Much of it (Engram protocol, SDD orchestrator) is only needed when those features activate.
4. **Command drift**: 4 duplicated project commands between `.claude/commands/` and `.opencode/commands/` -- if commit format changes, both must be updated.

---

## Part II: Solution Architecture

### 3. Project-Level Config Unification

The core problem: Claude Code reads `.claude/CLAUDE.md` and OpenCode reads `.opencode/AGENTS.md`. Neither reads the other's directory. Commands are duplicated between `.claude/commands/` and `.opencode/commands/`. Docs live only in `.claude/docs/` but OpenCode has no access to them.

The goal: a single source of truth for everything (config, commands, docs, skills) with symlinks from each tool's expected location.

#### The Architecture: `.agents/` at Project Root

Consistent with the global `~/.agents/` pattern — a `.agents/` directory at the project root holds everything. Both tools point to it via symlinks.

```
centro-control/
├── .agents/
│   ├── AGENTS.md          <-- project config + skill registry (source of truth)
│   ├── commands/          <-- all project commands (source of truth)
│   │   ├── commit.md
│   │   ├── pr.md
│   │   ├── test.md
│   │   ├── deploy-check.md
│   │   ├── new-module.md
│   │   └── update-docs.md
│   ├── docs/              <-- all project documentation (source of truth)
│   │   ├── architecture.md
│   │   ├── database.md
│   │   ├── module-system.md
│   │   ├── patterns.md
│   │   ├── testing.md
│   │   └── modules/
│   └── skills/            <-- project-specific skills (empty for now, ready to grow)
│
├── .claude/
│   ├── CLAUDE.md    -> ../.agents/AGENTS.md    <-- symlink
│   ├── commands/    -> ../.agents/commands/    <-- symlink
│   ├── docs/        -> ../.agents/docs/        <-- symlink
│   └── settings.local.json                     <-- tool-specific, stays here
│
└── .opencode/
    ├── AGENTS.md    -> ../.agents/AGENTS.md    <-- symlink
    ├── commands/    -> ../.agents/commands/    <-- symlink
    └── package.json                            <-- tool-specific, stays here
```

#### Why `.agents/` and Not the Repo Root

Putting `AGENTS.md` at the repo root pollutes it. `.agents/` keeps everything contained, mirrors the global `~/.agents/` pattern, and makes it clear what the directory is for. Any developer (or new tool) knows where to look.

#### What Goes in `.agents/AGENTS.md`

The project config file acts as both the agent instructions and the skill/doc registry:

```markdown
# centro-control

## Stack
FastAPI · SQLAlchemy · Pydantic v2 · PostgreSQL (multi-schema) · Alembic · Docker

## Critical Rules
- Never touch `app/core/auth/user.py` — User model relationships injected dynamically
- Never edit `.env` files — use `.env.example` only
- Service name in docker: `api` — always `docker-compose exec api <cmd>`
- Never commit directly to `main`
- Never skip hooks (`--no-verify`)

## Documentation (load on demand — do NOT pre-load)

| File | When to load |
|------|-------------|
| @docs/architecture.md | system overview, startup sequence, module installation |
| @docs/module-system.md | autodiscovery, manifest spec, automation contract |
| @docs/patterns.md | model/schema/service/router/exception conventions |
| @docs/database.md | multi-schema strategy, Alembic, migration conventions |
| @docs/testing.md | conftest hierarchy, fixtures, test commands |
| @docs/modules/README.md | module registry — what modules exist and their status |

## Skills (load on demand)

| Skill | Trigger |
|-------|---------|
| `new-module` | creating a new module from scratch |
| `python-domain-architect` | architecture decisions, module structure |
| `sdd-*` | any substantial feature — use `/sdd-new <name>` |

## Quick Reference
\`\`\`bash
docker-compose exec api pytest                          # full suite
docker-compose exec api pytest app/modules/<mod>/tests  # module tests
docker-compose exec api alembic upgrade head            # run migrations
docker-compose exec api alembic revision --autogenerate -m "<desc>"
\`\`\`
```

#### Lazy Loading: Both Tools

**Claude Code** — `@docs/architecture.md` is natively lazy: the file is only read when the agent decides it needs it during the conversation.

**OpenCode** — no native `@` syntax, but the table with "when to load" instructions tells the agent to use the Read tool on demand. Same result, different mechanism. The explicit `do NOT pre-load` instruction is respected by both.

#### Setting Up the Symlinks

```bash
cd ~/dev/Proyectos/centro-control

# 1. Create .agents/ structure
mkdir -p .agents/skills

# 2. Move existing content into .agents/
mv .claude/docs .agents/docs
mv .claude/commands .agents/commands
# Create AGENTS.md from current CLAUDE.md content (see template above)

# 3. Create symlinks for Claude Code
ln -sf ../.agents/AGENTS.md .claude/CLAUDE.md
ln -sf ../.agents/commands .claude/commands
ln -sf ../.agents/docs .claude/docs

# 4. Create symlinks for OpenCode
ln -sf ../.agents/AGENTS.md .opencode/AGENTS.md
ln -sf ../.agents/commands .opencode/commands

# 5. Verify
ls -la .claude/CLAUDE.md .claude/commands .claude/docs
ls -la .opencode/AGENTS.md .opencode/commands
```

> **Git & cloning**: Symlinks are tracked by git and preserved on clone. All symlink targets are inside the same repo, so they never break after cloning on another machine.

#### What Stays Separate (Tool-Specific, Not Unified)

| Item | Claude Code | OpenCode |
|------|------------|----------|
| Permissions | `.claude/settings.local.json` | `.opencode/opencode.json` |
| MCP config | `~/.claude/mcp/` (global) | `~/.config/opencode/opencode.json` (global) |
| Plugin config | `~/.claude/settings.json` (global) | `~/.config/opencode/opencode.json` (global) |

#### Why This Architecture

| Criteria | `.agents/` approach |
|----------|-------------------|
| Single source of truth | Yes — `.agents/` owns everything |
| No tool owns the config | Yes — neither `.claude/` nor `.opencode/` is canonical |
| Works with only one tool | Yes — symlinks exist in each tool's expected location |
| Zero duplication | Yes — commands and docs in one place |
| Lazy doc loading | Yes — `@docs/` refs with "do NOT pre-load" instruction |
| Consistent with global pattern | Yes — same `.agents/` convention as `~/.agents/` |
| Easy to add new tools | Yes — add two symlinks and done |
| Project-specific skills | Yes — `.agents/skills/` ready when needed |

---

### 4. Global Config Unification

#### 4.1 Target `~/.agents/` Structure

```
~/.agents/                          <-- NEW shared directory
├── PERSONA.md                      <-- personality, language, tone, philosophy, expertise, behavior, rules
├── ENGRAM_PROTOCOL.md              <-- engram save/search/session/compaction protocol
├── SDD_ORCHESTRATOR.md             <-- delegation rules, commands, dependency graph, context protocol
├── skills/                         <-- CANONICAL skill directory
│   ├── _shared/
│   │   ├── engram-convention.md
│   │   ├── openspec-convention.md
│   │   └── persistence-contract.md
│   ├── sdd-init/
│   ├── sdd-explore/
│   ├── sdd-propose/
│   ├── sdd-spec/
│   ├── sdd-design/
│   ├── sdd-tasks/
│   ├── sdd-apply/
│   ├── sdd-verify/
│   ├── sdd-archive/
│   ├── go-testing/
│   ├── skill-creator/
│   ├── create-issue/
│   ├── deploy-ios/
│   ├── status-cli-theme/
│   └── frontend-ui-ux-engineer/
└── shared/
    └── shared-context.md           <-- cross-repo project state

~/.claude/                          <-- LEAN entry point
├── CLAUDE.md                       <-- ~30 lines: @refs to ~/.agents/*.md
├── settings.json                   <-- unchanged (tool-specific)
├── skills/ -> ~/.agents/skills/    <-- SYMLINK
├── shared/ -> ~/.agents/shared/    <-- SYMLINK
├── mcp/                            <-- unchanged (tool-specific)
├── plugins/                        <-- unchanged (tool-specific)
├── commands/                       <-- unchanged (tool-specific)
└── projects/                       <-- unchanged (tool-specific)

~/.config/opencode/                 <-- LEAN entry point
├── AGENTS.md                       <-- ~30 lines: {file:} refs to ~/.agents/*.md
├── opencode.json                   <-- unchanged (tool-specific)
├── skills/ -> ~/.agents/skills/    <-- SYMLINK
├── commands/                       <-- unchanged (tool-specific)
└── plugins/                        <-- unchanged (tool-specific)
```

#### 4.2 PERSONA.md Content

See Section 13.1 for the complete file.

Core blocks extracted from current CLAUDE.md/AGENTS.md:
- Rules (~8 lines)
- Personality (~3 lines)
- Language (~3 lines)
- Tone (~3 lines)
- Philosophy (~5 lines)
- Expertise (~3 lines)
- Behavior (~5 lines)

Total: ~35 lines. Loaded ALWAYS (both tools need persona in every session).

#### 4.3 ENGRAM_PROTOCOL.md Content

See Section 13.2 for the complete file.

Core blocks extracted from current CLAUDE.md:
- Proactive save triggers (~25 lines)
- Format for mem_save (~10 lines)
- Topic update rules (~5 lines)
- When to search memory (~15 lines)
- Session close protocol (~15 lines)
- After compaction (~8 lines)

Total: ~80 lines. Loaded ON-DEMAND (only when engram MCP is available).

#### 4.4 SDD_ORCHESTRATOR.md Content

See Section 13.3 for the complete file.

Core blocks extracted from current CLAUDE.md:
- Delegation rules (~15 lines)
- Anti-patterns (~6 lines)
- Task escalation (~6 lines)
- Artifact store policy (~5 lines)
- Commands (~10 lines)
- Dependency graph (~10 lines)
- Sub-agent context protocol (~30 lines)
- Engram topic key format (~15 lines)
- Result contract (~2 lines)
- Recovery rule (~5 lines)
- State & conventions (~5 lines)

Total: ~110 lines. Loaded ON-DEMAND (only when SDD commands are invoked).

#### 4.5 Lean Entry Points

**Claude Code `~/.claude/CLAUDE.md` (~30 lines):**

```markdown
# Global Claude Code Config

## Project Identity
Centro Control -- personal modular platform. Backend FastAPI + frontend (separate repo).

## Active Repos
- `centro-control/` -- monorepo (backend + frontend). Backend in `centro-control/backend/`.

## Global Preferences
- Communication language: **Spanish (Rioplatense)**
- Commits: **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- Never commit directly to `main`
- Never skip hooks (`--no-verify`)
- Never touch `.env` -- only `.env.example`

## Cross-repo Context
@shared/shared-context.md

## Persona & Rules
@../../.agents/PERSONA.md

## Engram Protocol
@../../.agents/ENGRAM_PROTOCOL.md

## SDD Orchestrator
@../../.agents/SDD_ORCHESTRATOR.md

## Skills (Auto-load based on context)
IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
```

**OpenCode `~/.config/opencode/AGENTS.md` (~30 lines):**

```markdown
# Global OpenCode Config

{file:../../.agents/PERSONA.md}

{file:../../.agents/ENGRAM_PROTOCOL.md}

{file:../../.agents/SDD_ORCHESTRATOR.md}

## Skills (Auto-load based on context)
IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
```

#### 4.6 Skills Symlinks

After moving skills to `~/.agents/skills/`:

```bash
# Claude Code
ln -sf ~/.agents/skills ~/.claude/skills

# OpenCode
ln -sf ~/.agents/skills ~/.config/opencode/skills
```

Both tools resolve skills from the same physical directory. Adding a new skill once makes it available everywhere.

#### 4.7 Commands Consolidation

Commands are tool-specific in format and cannot be trivially shared. Strategy:

- **Global commands** (`~/.claude/commands/`, `~/.config/opencode/commands/`) -- remain separate, as they use different syntax and have different command sets.
- **Project commands** -- see Section 3 (Option B): `.claude/commands/` is canonical, `.opencode/commands/` contains thin wrappers.

This is acceptable because commands are small files (5-20 lines each) and rarely change.

#### 4.8 Tool-Specific Configs That Stay Separate

These files are inherently tool-specific and MUST NOT be unified:

| File | Tool | Why it stays |
|------|------|-------------|
| `~/.claude/settings.json` | Claude Code | Plugin marketplace, model selection, outputStyle, permissions format |
| `~/.claude/mcp/` | Claude Code | MCP server configs specific to Claude Code's plugin system |
| `~/.claude/plugins/` | Claude Code | Plugin data |
| `~/.claude/projects/` | Claude Code | Per-project session state |
| `~/.config/opencode/opencode.json` | OpenCode | Agent definitions, MCP configs, permission format |
| `~/.config/opencode/plugins/engram.ts` | OpenCode | TypeScript plugin specific to OpenCode |

---

### 5. Lazy Loading Strategy

#### 5.1 Three Loading Levels

| Level | When Loaded | Content | Justification |
|-------|-------------|---------|---------------|
| **ALWAYS** | Every session start | Persona, rules, global preferences, project identity | Agent behavior depends on these in every interaction |
| **ON-DEMAND** | When feature activates | Engram protocol, SDD orchestrator, architecture docs, module docs | Only needed when those workflows/modules are relevant |
| **NEVER inline** | Resolved by tool at access time | Individual skill SKILL.md files, shared conventions | Skills are loaded by the skill system when invoked |

#### 5.2 Before vs After Comparison

**Global CLAUDE.md:**

| Section | Before (lines) | After (lines) | Loading |
|---------|----------------|---------------|---------|
| Project identity + prefs | 15 | 15 | ALWAYS |
| Shared context ref | 1 | 1 | ALWAYS (lazy @ref) |
| Persona + rules | 50 | 1 (@ref) | ALWAYS (resolved) |
| Engram protocol | 80 | 1 (@ref) | ON-DEMAND |
| SDD orchestrator | 120 | 1 (@ref) | ON-DEMAND |
| Skills table | 10 | 10 | ALWAYS |
| **Total** | **~322** | **~30** | |

**Context savings**: ~290 lines not loaded until needed. Engram protocol (80 lines) only loads when `mem_*` tools are available. SDD orchestrator (120 lines) only loads when `/sdd-*` commands are invoked.

**Project CLAUDE.md (centro-control):**

| Section | Before (lines) | After (lines) | Loading |
|---------|----------------|---------------|---------|
| Stack + rules | 12 | 12 | ALWAYS |
| Conventions | 5 | 5 | ALWAYS |
| Architecture docs | 5 (@refs) | 5 (@refs) | ON-DEMAND (already lazy) |
| Module docs | 8 (@refs) | 8 (@refs) | ON-DEMAND (already lazy) |
| Quick reference | 6 | 6 | ALWAYS |
| **Total** | **41** | **~41** | Already lean |

The project-level CLAUDE.md is already well-optimized with lazy `@doc` references. No changes needed.

#### 5.3 How Each Tool Handles Lazy Loading

**Claude Code:**
- `@path/to/file.md` -- file is loaded into context when the agent encounters the reference. Claude Code resolves paths relative to the CLAUDE.md location.
- Skills: loaded via the built-in skill system when context matches the trigger pattern.
- Commands: loaded when the user types `/command-name`.

**OpenCode:**
- `{file:./path/to/file.md}` -- file content is inlined at parse time (before the agent sees it). This means ALL `{file:}` references are ALWAYS loaded.
- Skills: loaded manually via file references in agent prompts or commands.
- Commands: loaded when the user types `/command-name`.

**Implication for lazy loading**: Claude Code's `@ref` is truly lazy (loaded on access). OpenCode's `{file:}` is eager (loaded at parse time). For OpenCode, the lean AGENTS.md with `{file:}` refs will inline all three files (~225 lines total) -- still much better than the current 192-line monolith, because the content is now modular and maintainable even if loaded eagerly.

---

### 6. Skill Registry as Project Config

#### 6.1 Format Inspired by Gentleman.Dots AGENTS.md

The project-level config should serve as both a project overview and a skill/doc registry with auto-invoke triggers. This format combines the current `.claude/CLAUDE.md` structure with registry patterns.

#### 6.2 Example for centro-control

```markdown
# Centro Control -- Backend

## Stack
FastAPI . SQLAlchemy . Pydantic v2 . PostgreSQL (multi-schema) . Alembic . Docker

## Critical Rules
- **Never touch `app/core/auth/user.py`** -- User model has no module columns; relationships injected via manifest.py
- **Never edit .env files** -- use `.env.example` as reference only
- **CORS is `allow_origins=["*"]`** -- known issue, do not expand without fixing
- **Service name in docker is `api`** -- always `docker-compose exec api <cmd>`

## Branch & Commit Conventions
- Branches: `feat/<name>`, `fix/<name>`, `chore/<name>`
- Commits: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Never commit directly to `main`

## Architecture Registry

Auto-load these docs when working on the corresponding area:

| Context | Doc to load |
|---------|-------------|
| System design, startup, schemas | @docs/architecture.md |
| Module creation, manifest, autodiscovery | @docs/module-system.md |
| Models, schemas, services, routers, exceptions | @docs/patterns.md |
| Migrations, alembic, multi-schema | @docs/database.md |
| Tests, fixtures, conftest | @docs/testing.md |

## Module Registry

Auto-load when working on the specific module:

| Module | Schema | Automation | Doc |
|--------|--------|-----------|-----|
| gym_tracker | gym_tracker | Yes | @docs/modules/gym_tracker.md |
| expenses_tracker | expenses_tracker | Yes | @docs/modules/expenses_tracker.md |
| macro_tracker | macro_tracker | No | @docs/modules/macro_tracker.md |
| flights_tracker | flights_tracker | Yes | @docs/modules/flights_tracker.md |
| travels_tracker | travels_tracker | No | @docs/modules/travels_tracker.md |
| calendar_tracker | calendar_tracker | Yes (ref) | @docs/modules/calendar_tracker.md |
| automations_engine | automations | N/A (engine) | @docs/modules/automations_engine.md |

## Quick Reference
docker-compose exec api pytest                          # full suite
docker-compose exec api pytest app/modules/<mod>/tests  # module tests
docker-compose exec api alembic upgrade head             # run migrations
docker-compose exec api alembic revision --autogenerate -m "<desc>"
```

#### 6.3 Lazy Doc References

Each `@docs/...` reference is only resolved when the agent needs that context. This means:
- Working on a gym_tracker bug only loads `gym_tracker.md` + `patterns.md`
- Creating a new module loads `module-system.md` + `patterns.md` + `database.md`
- Running tests loads `testing.md`

The agent decides what to load based on the user's request. The registry tells it WHERE to find each doc.

---

### 7. Risk Analysis & Safety Guarantees

#### 7.1 Component Dependency Map

```
                          ~/.agents/
                         /    |     \
                        /     |      \
                       v      v       v
              PERSONA.md  ENGRAM_    SDD_
                          PROTOCOL   ORCHESTRATOR
                           .md         .md
                            |            |
                            v            v
                     Engram MCP    SDD Skills
                     tools         (sdd-init,
                     (mem_*)       sdd-explore,
                            |      etc.)
                            v        |
                     settings.json   v
                     (permissions,  _shared/
                      plugins)     (conventions)
                            |
                            v
                     Plugin system
                     (engram plugin,
                      skill-creator)
```

**Dependency chains (what feeds what):**

| Component | Depends On | Feeds Into |
|-----------|-----------|------------|
| **Engram MCP** | `engram` binary on PATH, MCP config in `settings.json` (Claude) / `opencode.json` (OpenCode) | `mem_*` tools available to agent |
| **Engram Protocol** | `ENGRAM_PROTOCOL.md` content loaded into agent context | Agent knows WHEN and HOW to use `mem_*` tools |
| **Plugins** | `settings.json` -> `enabledPlugins` | Plugin features (engram marketplace, skill-creator) |
| **Persona** | `PERSONA.md` content in agent context | Agent personality, language, tone in every response |
| **SDD Orchestrator** | `SDD_ORCHESTRATOR.md` content + SDD skills in `skills/` + `_shared/` conventions | Delegation behavior, `/sdd-*` command handling |
| **Agent Teams Lite** | Orchestrator section in SDD_ORCHESTRATOR.md | Sub-agent delegation for ALL tasks (not just SDD) |
| **Skills** | `skills/` directory readable by tool | Skill auto-loading when context matches |
| **Commands** | `commands/*.md` in tool-specific dir | `/commit`, `/pr`, `/test` etc. |
| **Shared Context** | `shared/shared-context.md` readable | Cross-repo state awareness |
| **Project Docs** | `.claude/docs/*.md` readable | Architecture/module knowledge |

#### 7.2 What Can Break Per Migration Step

| Migration Step | What Breaks If Done Wrong | Detection |
|----------------|--------------------------|-----------|
| Extract PERSONA.md from CLAUDE.md | Agent loses personality, responds in English instead of Rioplatense Spanish, loses confrontational tone | First response in session lacks personality |
| Extract ENGRAM_PROTOCOL.md | Agent stops proactively saving to engram, loses session close protocol | No `mem_save` calls after decisions, no `mem_session_summary` at end |
| Extract SDD_ORCHESTRATOR.md | Agent does work inline instead of delegating, SDD commands fail | Agent reads code directly, `/sdd-new` does not launch sub-agent |
| Symlink `skills/` | Skills stop loading if symlink target does not exist or is broken | `/sdd-init` or skill auto-load fails with "skill not found" |
| Symlink `shared/` | `@shared/shared-context.md` fails to resolve | Agent has no cross-repo context |
| Modify `opencode.json` | Agent definitions, MCP connections break | OpenCode fails to start or engram tools unavailable |
| Modify `settings.json` | Permissions, plugins, model selection break | Claude Code denies engram tools or uses wrong model |
| Change `.opencode/commands/` | `/commit`, `/pr` stop working or produce wrong output | Command invocation returns error or generates wrong format |

#### 7.3 Rollback Guarantees

Every phase has an exact rollback command. The backup (Phase 0) ensures nuclear rollback is always available. See Section 18 for complete rollback procedures.

**Principle**: Each phase is independently rollback-able. If Phase 2 breaks something, rolling back Phase 2 does NOT undo Phase 1.

#### 7.4 Incremental Approach

```
Phase 0: Backup (5 min)
    |
    v
Phase 1: Project-level wrappers (10 min)
    |-- VERIFY: both tools work with project --+
    |                                          |
    v                                     ROLLBACK if broken
Phase 2: Global skills consolidation (15 min)
    |-- VERIFY: skills load in both tools --+
    |                                       |
    v                                  ROLLBACK if broken
Phase 3: Global entry points (20 min)
    |-- VERIFY: persona, engram, SDD work --+
    |                                       |
    v                                  ROLLBACK if broken
DONE
```

Each phase has a verification checklist. Do NOT proceed to the next phase until the current phase passes all checks.

#### 7.5 "Don't Touch What Works" Principle

These files are NOT modified during migration:

- `~/.claude/settings.json` -- permissions, plugins, model stay as-is
- `~/.config/opencode/opencode.json` -- agents, MCP, permissions stay as-is
- `~/.claude/mcp/` -- MCP server configs stay as-is
- `~/.claude/plugins/` -- plugin data stays as-is
- `~/.config/opencode/plugins/engram.ts` -- OpenCode plugin stays as-is
- `.claude/docs/` -- all 13 docs stay as-is
- `.claude/settings.local.json` -- project permissions stay as-is
- `~/.local/share/engram/engram.db` -- engram database is never touched

---

## Part III: PRD -> TDD -> SDD Integrated Workflow

### 8. Workflow Overview

#### 8.1 When to Use

| Scenario | Workflow |
|----------|----------|
| Quick bug fix, single file | Direct fix, no workflow needed |
| Small enhancement (1-3 files) | Optional: write test first, then implement |
| New module or substantial feature | **Full PRD -> TDD -> SDD pipeline** |
| Architecture change or refactor | **Full PRD -> TDD -> SDD pipeline** |
| Cross-module integration | **Full PRD -> TDD -> SDD pipeline** |

Rule of thumb: if the change touches more than 3 files or introduces new concepts, use the full pipeline.

#### 8.2 Three Phases

```
Phase 1: PRD                    Phase 2: TDD                    Phase 3: SDD
(What to build)                 (How to verify)                 (How to build)

/new-prd <feature>              Write failing tests             /sdd-new <feature>
    |                           from PRD requirements               |
    v                               |                               v
docs/prd/<feature>.md           app/modules/<mod>/tests/        proposal -> spec ->
    |                           test_<feature>.py                design -> tasks ->
    |  20 sections filled           |                           apply -> verify
    |  with requirements            v
    |                           RED: all tests fail
    |                               |
    +------ feeds into ------------>+------ feeds into -------> sdd-apply uses TDD:
                                                                test -> red ->
                                                                implement -> green ->
                                                                refactor
```

#### 8.3 Dependency Graph

```
    PRD
     |
     | requirements
     |
     v
    TDD (failing tests)
     |
     | test suite + PRD
     |
     v
  SDD Proposal
     |
     +--------+
     |        |
     v        v
   Spec    Design
     |        |
     +---+----+
         |
         v
       Tasks
         |
         v
     Apply (with TDD loop: RED -> GREEN -> REFACTOR)
         |
         v
     Verify (all TDD tests must pass)
         |
         v
     Archive
```

#### 8.4 Command Reference

| Command | Phase | What it does |
|---------|-------|-------------|
| `/new-prd <feature>` | PRD | Creates PRD from template, guides through 20 sections |
| (manual) | TDD | Write failing tests from PRD requirements |
| `/sdd-new <feature>` | SDD | Creates exploration + proposal from PRD |
| `/sdd-ff <feature>` | SDD | Fast-forwards through proposal -> spec -> design -> tasks |
| `/sdd-apply <feature>` | SDD | Implements tasks with TDD loop |
| `/sdd-verify <feature>` | SDD | Verifies implementation against spec + runs all tests |
| `/sdd-archive <feature>` | SDD | Archives completed change |

---

### 9. Phase 1: PRD (Product Requirements Document)

#### 9.1 The `/new-prd` Command Concept

The `/new-prd` command creates a structured PRD file at `docs/prd/<feature-name>.md` using the 20-section template. It guides the user through each section, asking clarifying questions when requirements are ambiguous.

**Invocation**: `/new-prd <feature-name>`
**Output**: `docs/prd/<feature-name>.md`
**Storage**: PRDs live in `docs/prd/` within the project repo, versioned with git.

#### 9.2 PRD Template -- All 20 Sections

##### Section 1: Core Vision

**Purpose**: One-paragraph description of what the feature does and why it matters.

**Guidance**:
- Answer: "What problem does this solve and for whom?"
- Keep it to 3-5 sentences maximum.
- Include the business value, not just the technical description.
- Example: "A notification system that alerts users when calendar events are approaching, using Firebase Cloud Messaging to push notifications to mobile devices. This reduces missed appointments and keeps the user's day organized without requiring them to constantly check the app."

##### Section 2: Problem It Solves

**Purpose**: The specific gap or pain point this feature addresses.

**Guidance**:
- List concrete problems as bullet points.
- Each problem should be observable and measurable.
- Include who is affected and how.
- Format:
  ```
  - Problem: [description]
    Impact: [who is affected, how badly]
    Current workaround: [what users do today, or "none"]
  ```

##### Section 3: Key Components

**Purpose**: Major subsystems or modules that make up this feature.

**Guidance**:
- List 3-7 components with one-sentence descriptions.
- Show how they relate to each other.
- Map to the module structure of centro-control (models, services, routers, etc.).
- Example:
  ```
  - **NotificationService**: Manages notification lifecycle (create, send, mark read)
  - **FCM Integration**: Handles Firebase Cloud Messaging API communication
  - **Scheduler Job**: Periodic check for upcoming events that need notifications
  ```

##### Section 4: Supported Platforms/Integrations

**Purpose**: Matrix of what works where, and what integrations are supported.

**Guidance**:
- Table format showing feature support across platforms/integrations.
- For centro-control, this maps to: which modules interact with this feature, which external APIs are involved, which frontends consume it.
- Example:
  ```
  | Integration | Status | Notes |
  |-------------|--------|-------|
  | Web frontend | Full | All CRUD + real-time |
  | Mobile (Capacitor) | Partial | Push notifications only |
  | Google Calendar | Full | Bi-directional sync |
  | Apple Calendar | Read-only | CalDAV pull only |
  ```

##### Section 5: Dependency Management Strategy

**Purpose**: How dependencies are resolved and what the critical dependency list is.

**Guidance**:
- List Python packages needed (with version constraints if relevant).
- List external services required (APIs, databases, message brokers).
- Note any dependency on other centro-control modules.
- Distinguish between hard dependencies (required) and soft dependencies (optional/degraded mode).
- Example:
  ```
  Hard dependencies:
  - SQLAlchemy (existing) -- ORM for persistence
  - APScheduler (existing) -- scheduler jobs

  Soft dependencies:
  - firebase-admin -- push notifications (graceful degradation: log instead of push)

  Module dependencies:
  - automations_engine -- for automation contract integration
  ```

##### Section 6: User Flow / Setup Flow

**Purpose**: Step-by-step user journey through the feature.

**Guidance**:
- Numbered steps from the user's perspective.
- Include both happy path and error paths.
- Map to API endpoints where applicable.
- Example:
  ```
  1. User registers FCM token via POST /api/v1/notifications/tokens
  2. User creates event with notification preference
  3. Scheduler detects upcoming event (advance_minutes before start)
  4. System sends push notification via FCM
  5. User taps notification -> opens app -> navigates to event
  ```

##### Section 7: Configuration Coverage Matrix

**Purpose**: What gets configured/created for each component.

**Guidance**:
- Table showing all configuration points.
- Include env vars, database records, manifest entries, and runtime configuration.
- Example:
  ```
  | Component | Config Type | Key | Default | Required |
  |-----------|-------------|-----|---------|----------|
  | Firebase | env var | FIREBASE_CREDENTIALS_JSON | - | Yes |
  | Scheduler | code | check_interval_minutes | 5 | No |
  | Manifest | manifest.py | SCHEMA_NAME | - | Yes |
  ```

##### Section 8: Technology Stack

**Purpose**: Languages, frameworks, tools, and infrastructure used.

**Guidance**:
- Inherit the project stack (FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL, Docker).
- List only ADDITIONS to the existing stack.
- Include version constraints if they matter.
- Example:
  ```
  Inherited: FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL (multi-schema), Alembic, Docker
  New: firebase-admin >= 6.0 (FCM push notifications)
  ```

##### Section 9: Package Structure

**Purpose**: Proposed directory layout for the feature.

**Guidance**:
- Follow centro-control module conventions (see `@docs/patterns.md`).
- Use gym_tracker as the reference structure for complex modules.
- Use expenses_tracker as the reference for simpler modules.
- Example:
  ```
  my_module/
  +-- manifest.py
  +-- models/
  +-- schemas/
  +-- services/
  +-- routers/
  +-- exceptions/
  +-- handlers/
  +-- automation_registry.py    (if automation contract)
  +-- automation_handlers.py
  +-- automation_dispatcher.py
  +-- scheduler_service.py      (if periodic jobs)
  +-- tests/
  ```

##### Section 10: API / Interface Contract

**Purpose**: Endpoint definitions, request/response schemas, and contracts.

**Guidance**:
- List all endpoints with method, path, request body, response body, and status codes.
- Use Pydantic schema naming conventions (Create, Update, Response, DetailResponse).
- Include authentication requirements.
- Example:
  ```
  POST /api/v1/my-resource/
    Auth: required
    Body: MyResourceCreate
    Response: 201 MyResourceResponse
    Errors: 400 (validation), 409 (conflict)

  GET /api/v1/my-resource/{id}
    Auth: required
    Response: 200 MyResourceDetailResponse
    Errors: 404 (not found), 403 (not yours)
  ```

##### Section 11: Configuration Presets / Defaults

**Purpose**: Pre-built configurations and sensible defaults.

**Guidance**:
- List all configurable values with their defaults.
- Explain the rationale for each default.
- Note which defaults can be overridden by the user at runtime.
- Example:
  ```
  | Setting | Default | Rationale | User-configurable |
  |---------|---------|-----------|-------------------|
  | advance_minutes | 15 | Standard reminder time | Yes (per event) |
  | max_retries | 3 | Balance between reliability and spam | No |
  | batch_size | 50 | Memory/performance tradeoff | No |
  ```

##### Section 12: Deployment / Distribution

**Purpose**: How the feature ships and what deployment steps are needed.

**Guidance**:
- Alembic migration required? Describe the schema changes.
- New env vars needed? List them for `.env.example`.
- Docker changes? New services or dependencies.
- Railway-specific considerations (see `get_settings()` pattern in `@docs/patterns.md`).
- Example:
  ```
  1. Add env vars to .env.example: FIREBASE_CREDENTIALS_JSON
  2. Generate migration: alembic revision --autogenerate -m "add_notifications"
  3. No new Docker services needed
  4. Railway: ensure FIREBASE_CREDENTIALS_JSON is set in environment
  ```

##### Section 13: External Integrations / Providers

**Purpose**: Third-party services used, their APIs, and authentication.

**Guidance**:
- List each external service with: name, purpose, auth method, rate limits, cost.
- Include the client code pattern (see existing modules: `aerodatabox_client.py`, `openfoodfacts_client.py`).
- Note graceful degradation strategy.
- Example:
  ```
  | Provider | Purpose | Auth | Rate Limit | Cost |
  |----------|---------|------|------------|------|
  | Firebase FCM | Push notifications | Service account JSON | 500k/day | Free |
  | Open Food Facts | Product lookup | None (open API) | Unlimited | Free |
  ```

##### Section 14: Expected End State

**Purpose**: What exists after implementation is complete.

**Guidance**:
- Concrete list of artifacts that will exist.
- Include: files created, database tables, API endpoints available, scheduler jobs running.
- This is the "definition of done" checklist.
- Example:
  ```
  After implementation:
  - [ ] 3 new models in `notifications` schema
  - [ ] 5 new API endpoints under /api/v1/notifications/
  - [ ] 1 scheduler job checking every 5 minutes
  - [ ] Automation contract: 2 triggers, 1 action registered
  - [ ] Migration applied, tables created
  - [ ] Tests passing (>= 90% coverage on new code)
  ```

##### Section 15: Non-Functional Requirements

**Purpose**: Performance, security, reliability, extensibility, and accessibility requirements.

**Guidance**:
- Use table format with requirement, target, and measurement method.
- Be specific and measurable.

  ```
  ## Performance
  | Requirement | Target | Measurement |
  |-------------|--------|-------------|
  | API response time | < 200ms p95 | Load test with k6 |
  | Scheduler cycle time | < 30s per cycle | APScheduler logs |

  ## Security
  | Requirement | Implementation |
  |-------------|---------------|
  | User isolation | All queries filter by user_id |
  | Token encryption | ENCRYPTION_KEY for OAuth tokens |

  ## Reliability
  | Requirement | Strategy |
  |-------------|----------|
  | FCM failure | Log + retry up to 3 times |
  | DB connection loss | SQLAlchemy connection pool auto-reconnect |

  ## Extensibility
  | Requirement | Approach |
  |-------------|----------|
  | New notification channels | Strategy pattern in notification_service |
  | New trigger types | Automation contract (register_trigger) |
  ```

##### Section 16: Relationship to Existing System

**Purpose**: How this feature interacts with current modules and architecture.

**Guidance**:
- Which existing modules are affected?
- Are there changes to shared infrastructure (User model relationships, startup sequence)?
- Does this feature add to the automation contract?
- Any impact on existing tests?
- Example:
  ```
  Touches:
  - manifest.py: adds USER_RELATIONSHIPS for new models
  - main.py: adds start_my_scheduler() to startup_event
  - calendar_tracker: new trigger fires when events approach

  Does NOT touch:
  - User model (relationships injected via manifest)
  - Existing module tests
  - CORS configuration
  ```

##### Section 17: Management / Maintenance

**Purpose**: How to update, repair, and check status of this feature post-deployment.

**Guidance**:
- Include health check endpoints or commands.
- Describe log monitoring points.
- List common failure modes and their resolution.
- Example:
  ```
  Health check:
  - GET /api/v1/notifications/health -> {"status": "ok", "pending": 5}

  Monitoring:
  - APScheduler logs: look for "job_check_notifications" execution times
  - FCM delivery logs: look for "fcm_send_failed" entries

  Common issues:
  - "FCM token expired" -> user must re-register token (automatic on app open)
  - "Scheduler not running" -> check startup_event in main.py
  ```

##### Section 18: Success Metrics

**Purpose**: KPIs and measurable outcomes that indicate the feature works.

**Guidance**:
- Define 3-5 concrete metrics.
- Include both technical metrics (response time, error rate) and user metrics (adoption, usage).
- Example:
  ```
  | Metric | Target | Timeframe |
  |--------|--------|-----------|
  | Notification delivery rate | > 95% | Per day |
  | API error rate | < 1% | Per day |
  | Average user notifications/day | > 3 | After 1 week |
  | Push notification open rate | > 30% | After 1 month |
  ```

##### Section 19: Open Questions

**Purpose**: Unresolved design decisions that need input.

**Guidance**:
- List each question with context and options.
- Tag with priority (blocking, can-defer, nice-to-know).
- Example:
  ```
  1. [BLOCKING] Should notifications be stored permanently or TTL-based?
     - Option A: Keep forever (simple, but table grows)
     - Option B: 30-day TTL with cleanup job (adds complexity)

  2. [CAN-DEFER] Should we support notification grouping?
     - Not needed for MVP, but useful for high-frequency triggers
  ```

##### Section 20: Future Scope

**Purpose**: Items explicitly out of scope for this version, planned for later.

**Guidance**:
- List features that were considered but deferred.
- Explain WHY they are deferred (complexity, dependencies, not enough data).
- This prevents scope creep during implementation.
- Example:
  ```
  Deferred to v2:
  - Email notifications (requires email service integration)
  - Notification preferences per category (needs UX research)
  - Rich push notifications with images (FCM supports it, but frontend needs work)

  Deferred indefinitely:
  - SMS notifications (cost, regulatory complexity)
  ```

#### 9.3 Storage Convention

```
centro-control/
└── docs/
    └── prd/
        ├── notification-system.md
        ├── habit-tracker.md
        └── ...
```

PRDs are versioned with git and live in the project repo. They are NOT stored in `.claude/docs/` (those are architecture/module docs, not requirements docs).

#### 9.4 PRD Quality Checklist

Before considering a PRD complete:

- [ ] All 20 sections have content (even if some are "N/A -- reason")
- [ ] Section 2 (Problem) has measurable impacts
- [ ] Section 10 (API) has concrete endpoints with schemas
- [ ] Section 14 (End State) has a checklist of deliverables
- [ ] Section 15 (Non-Functional) has measurable targets
- [ ] Section 16 (Relationship) identifies all touched modules
- [ ] Section 19 (Open Questions) has no BLOCKING items unresolved

---

### 10. Phase 2: TDD (Test-Driven Development)

#### 10.1 From PRD to Tests -- Mapping

| PRD Section | Test Category | What to Test |
|-------------|--------------|-------------|
| 2. Problem It Solves | Acceptance tests | Each problem statement becomes a test scenario |
| 6. User Flow | Integration tests | Each step in the flow becomes a test case |
| 10. API Contract | API tests | Each endpoint with valid/invalid inputs, auth, ownership |
| 14. End State | Smoke tests | Each deliverable has a verification test |
| 15. Non-Functional | Performance/security tests | Response time, user isolation, error handling |
| 16. Relationship | Regression tests | Existing module tests still pass |

#### 10.2 Test Architecture Recap (centro-control conventions)

**Conftest hierarchy:**
```
backend/
+-- conftest.py                          <-- root: db, client, auth_client, other_auth_client
+-- app/modules/<mod>/tests/
    +-- conftest.py                      <-- module: data fixtures via API calls
    +-- test_<feature>.py                <-- test files
```

**Key conventions:**
- Create data via API (`auth_client.post(...)`), NOT direct ORM insertion
- Function-scoped fixtures (clean state per test)
- Cleanup via `TRUNCATE TABLE core.users RESTART IDENTITY CASCADE`
- No hardcoded IDs -- use chained fixtures
- Ownership tests with `other_auth_client` (user B cannot access user A's data)

**Execution:**
```bash
docker-compose exec api pytest app/modules/<mod>/tests -v
```

#### 10.3 Writing Failing Tests from PRD (RED Phase)

The goal is to write tests that encode the PRD requirements BEFORE any implementation exists. These tests will all fail (RED). The SDD apply phase will make them pass (GREEN).

**Step-by-step process:**

1. **Create test file**: `app/modules/<mod>/tests/test_<feature>.py`
2. **Create module conftest** (if new module): `app/modules/<mod>/tests/conftest.py`
3. **Write fixtures** that create prerequisite data via API
4. **Write test functions** that assert the expected behavior

**Example -- from PRD Section 10 (API Contract):**

```python
# PRD says: POST /api/v1/my-resource/ returns 201 with MyResourceResponse
class TestCreateMyResource:
    def test_create_returns_201(self, auth_client, sample_data):
        response = auth_client.post("/api/v1/my-resource/", json=sample_data)
        assert response.status_code == 201

    def test_create_returns_expected_fields(self, auth_client, sample_data):
        response = auth_client.post("/api/v1/my-resource/", json=sample_data)
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_data["name"]

    def test_create_without_auth_returns_401(self, client, sample_data):
        response = client.post("/api/v1/my-resource/", json=sample_data)
        assert response.status_code == 401

# PRD says: GET /api/v1/my-resource/{id} returns 403 for other user's resource
class TestMyResourceOwnership:
    def test_other_user_cannot_access(self, auth_client, other_auth_client, sample_data):
        # User A creates resource
        create_resp = auth_client.post("/api/v1/my-resource/", json=sample_data)
        resource_id = create_resp.json()["id"]
        # User B tries to access it
        get_resp = other_auth_client.get(f"/api/v1/my-resource/{resource_id}")
        assert get_resp.status_code in (403, 404)
```

**Example -- from PRD Section 15 (Non-Functional):**

```python
# PRD says: All queries must filter by user_id
class TestUserIsolation:
    def test_list_only_returns_own_resources(self, auth_client, other_auth_client, sample_data):
        # User A creates 2 resources
        auth_client.post("/api/v1/my-resource/", json=sample_data)
        auth_client.post("/api/v1/my-resource/", json=sample_data)
        # User B creates 1 resource
        other_auth_client.post("/api/v1/my-resource/", json=sample_data)
        # User A should see only 2
        response = auth_client.get("/api/v1/my-resource/")
        assert len(response.json()) == 2
```

#### 10.4 Test File Conventions

| Convention | Rule |
|-----------|------|
| File naming | `test_<feature>.py` or `test_<entity>.py` |
| Class naming | `TestCreate<Entity>`, `TestGet<Entity>`, `Test<Entity>Ownership` |
| Function naming | `test_<action>_<expected_result>` |
| Fixture naming | `sample_<entity>_data`, `<entity>_id`, `active_<entity>_id` |
| Assertions | One logical assertion per test (multiple `assert` OK if testing same concept) |
| Test independence | Each test must work in isolation (no ordering dependency) |

---

### 11. Phase 3: SDD with TDD Integration

#### 11.1 SDD Lifecycle Recap

```
/sdd-new <feature>
    |
    v
Exploration (optional) -> Proposal -> Spec + Design -> Tasks -> Apply -> Verify -> Archive
```

Each phase produces an artifact stored in engram (default) or openspec files. Sub-agents execute each phase with fresh context, reading previous artifacts as dependencies.

#### 11.2 PRD Feeds the Proposal

When running `/sdd-new <feature>` after a PRD exists:

1. The orchestrator searches for `docs/prd/<feature>.md`
2. The `sdd-propose` sub-agent receives the PRD as context
3. The proposal references PRD sections for requirements, scope, and constraints
4. The spec phase maps PRD Section 10 (API) to detailed specifications
5. The design phase maps PRD Section 9 (Package Structure) to architecture decisions

**Key mapping:**

| PRD Section | SDD Artifact |
|-------------|-------------|
| 1. Core Vision | Proposal -> intent |
| 2. Problem + 3. Components | Proposal -> scope |
| 5. Dependencies | Design -> dependency decisions |
| 9. Package Structure | Design -> file layout |
| 10. API Contract | Spec -> requirements + scenarios |
| 15. Non-Functional | Spec -> non-functional requirements |
| 16. Relationship | Design -> integration points |

#### 11.3 TDD Loop Within `sdd-apply`

The `sdd-apply` phase implements tasks. With TDD integration, each task follows the RED-GREEN-REFACTOR cycle:

```
For each task in the task list:
    1. CHECK: Does a failing test exist for this task?
       - YES -> proceed to implementation
       - NO -> write the test first (from PRD requirements)

    2. RED: Run the test, confirm it fails
       docker-compose exec api pytest app/modules/<mod>/tests/test_<feature>.py -v

    3. GREEN: Write minimum code to make the test pass
       - Follow centro-control patterns (model, schema, service, router)
       - Follow the spec and design from SDD

    4. REFACTOR: Clean up without changing behavior
       - Extract helpers
       - Align naming with conventions
       - Run tests again to confirm still green

    5. COMMIT: Stage changes (do NOT commit -- wait for user /commit)
```

#### 11.4 `sdd-verify` Enhanced: All TDD Tests Must Pass

The `sdd-verify` phase is enhanced to include:

1. **Spec compliance check** (existing): implementation matches spec scenarios
2. **Design compliance check** (existing): architecture follows design decisions
3. **TDD test suite** (NEW): ALL tests in `test_<feature>.py` must pass
4. **Regression check** (NEW): full test suite passes (`docker-compose exec api pytest`)

```bash
# sdd-verify runs these checks:
docker-compose exec api pytest app/modules/<mod>/tests/test_<feature>.py -v  # feature tests
docker-compose exec api pytest                                                # full regression
```

If any test fails, `sdd-verify` reports `status: failed` with the failing test details.

---

### 12. End-to-End Example

**Scenario**: Adding a `habit_tracker` module to centro-control.

#### Step 1: PRD

```
/new-prd habit-tracker
```

Creates `docs/prd/habit-tracker.md` with all 20 sections filled:
- Core Vision: "Track daily habits with streaks and completion history"
- Problem: "No way to track recurring personal goals"
- Key Components: HabitService, StreakCalculator, SchedulerJob
- API Contract: CRUD endpoints for habits, POST for check-ins, GET for streaks
- Package Structure: follows gym_tracker reference structure
- etc.

#### Step 2: TDD (Write Failing Tests)

Create `backend/app/modules/habit_tracker/tests/conftest.py`:

```python
import pytest

@pytest.fixture
def sample_habit_data():
    return {"name": "Morning meditation", "frequency": "daily"}

@pytest.fixture
def habit_id(auth_client, sample_habit_data):
    response = auth_client.post("/api/v1/habits/", json=sample_habit_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]
```

Create `backend/app/modules/habit_tracker/tests/test_habits.py`:

```python
class TestCreateHabit:
    def test_create_habit_returns_201(self, auth_client, sample_habit_data):
        response = auth_client.post("/api/v1/habits/", json=sample_habit_data)
        assert response.status_code == 201

    def test_create_habit_has_id_and_name(self, auth_client, sample_habit_data):
        response = auth_client.post("/api/v1/habits/", json=sample_habit_data)
        data = response.json()
        assert "id" in data
        assert data["name"] == "Morning meditation"

class TestCheckIn:
    def test_checkin_increments_streak(self, auth_client, habit_id):
        auth_client.post(f"/api/v1/habits/{habit_id}/checkin")
        response = auth_client.get(f"/api/v1/habits/{habit_id}")
        assert response.json()["current_streak"] == 1

class TestHabitOwnership:
    def test_other_user_cannot_see_habits(self, auth_client, other_auth_client, sample_habit_data):
        auth_client.post("/api/v1/habits/", json=sample_habit_data)
        response = other_auth_client.get("/api/v1/habits/")
        assert len(response.json()) == 0
```

Run tests -- all should fail (RED):
```bash
docker-compose exec api pytest app/modules/habit_tracker/tests -v
# Expected: ALL FAIL (module doesn't exist yet)
```

#### Step 3: SDD

```
/sdd-new habit-tracker
```

The SDD pipeline receives:
- PRD from `docs/prd/habit-tracker.md`
- Failing test suite from `app/modules/habit_tracker/tests/`

It generates:
- **Proposal**: Intent (habit tracking), scope (CRUD + check-ins + streaks), approach
- **Spec**: Detailed requirements mapped from PRD Section 10
- **Design**: Architecture decisions (flat structure like expenses_tracker, streak calculation algorithm)
- **Tasks**: Ordered implementation checklist

```
/sdd-apply habit-tracker
```

For each task, the apply phase:
1. Checks the failing test for that task
2. Implements the minimum code (model, schema, service, router)
3. Runs the test -- confirms GREEN
4. Moves to next task

```
/sdd-verify habit-tracker
```

Runs:
1. Feature tests: `pytest app/modules/habit_tracker/tests -v` -- all GREEN
2. Full regression: `pytest` -- all GREEN
3. Spec compliance: implementation matches spec
4. Reports: `status: success`

---

## Part IV: Ready-to-Use Templates & Files

### 13. Global Config Files

#### 13.1 `~/.agents/PERSONA.md` -- Complete File Content

```markdown
# Persona & Rules

## Rules

- NEVER add "Co-Authored-By" or any AI attribution to commits. Use conventional commits format only.
- Never build after changes.
- When asking user a question, STOP and wait for response. Never continue or assume answers.
- Never agree with user claims without verification. Say "dejame verificar" and check code/docs first.
- If user is wrong, explain WHY with evidence. If you were wrong, acknowledge with proof.
- Always propose alternatives with tradeoffs when relevant.
- Verify technical claims before stating them. If unsure, investigate first.

## Personality

Senior Architect, 15+ years experience, GDE & MVP. Passionate educator frustrated with mediocrity and shortcut-seekers. Goal: make people learn, not be liked.

## Language

- Spanish input -> Rioplatense Spanish: laburo, ponete las pilas, boludo, quilombo, banca, dale, dejate de joder, ni en pedo, esta piola
- English input -> Direct, no-BS: dude, come on, cut the crap, seriously?, let me be real

## Tone

Direct, confrontational, no filter. Authority from experience. Frustration with "tutorial programmers". Talk like mentoring a junior you're saving from mediocrity. Use CAPS for emphasis.

## Philosophy

- CONCEPTS > CODE: Call out people who code without understanding fundamentals
- AI IS A TOOL: We are Tony Stark, AI is Jarvis. We direct, it executes.
- SOLID FOUNDATIONS: Design patterns, architecture, bundlers before frameworks
- AGAINST IMMEDIACY: No shortcuts. Real learning takes effort and time.

## Expertise

Frontend (Angular, React), state management (Redux, Signals, GPX-Store), Clean/Hexagonal/Screaming Architecture, TypeScript, testing, atomic design, container-presentational pattern, LazyVim, Tmux, Zellij.

## Behavior

- Push back when user asks for code without context or understanding
- Use Iron Man/Jarvis and construction/architecture analogies
- Correct errors ruthlessly but explain WHY technically
- For concepts: (1) explain problem, (2) propose solution with examples, (3) mention tools/resources
```

#### 13.2 `~/.agents/ENGRAM_PROTOCOL.md` -- Complete File Content

```markdown
# Engram Persistent Memory -- Protocol

You have access to Engram, a persistent memory system that survives across sessions and compactions.
This protocol is MANDATORY and ALWAYS ACTIVE -- not something you activate on demand.

## PROACTIVE SAVE TRIGGERS (mandatory -- do NOT wait for user to ask)

Call `mem_save` IMMEDIATELY and WITHOUT BEING ASKED after any of these:

### After decisions or conventions
- Architecture or design decision made
- Team convention documented or established
- Workflow change agreed upon
- Tool or library choice made with tradeoffs

### After completing work
- Bug fix completed (include root cause)
- Feature implemented with non-obvious approach
- Notion/Jira/GitHub artifact created or updated with significant content
- Configuration change or environment setup done

### After discoveries
- Non-obvious discovery about the codebase
- Gotcha, edge case, or unexpected behavior found
- Pattern established (naming, structure, convention)
- User preference or constraint learned

### Self-check -- ask yourself after EVERY task:
> "Did I just make a decision, fix a bug, learn something non-obvious, or establish a convention? If yes, call mem_save NOW."

## Format for `mem_save`

- **title**: Verb + what -- short, searchable (e.g. "Fixed N+1 query in UserList", "Chose Zustand over Redux")
- **type**: bugfix | decision | architecture | discovery | pattern | config | preference
- **scope**: `project` (default) | `personal`
- **topic_key** (optional but recommended for evolving topics): stable key like `architecture/auth-model`
- **content**:
  **What**: One sentence -- what was done
  **Why**: What motivated it (user request, bug, performance, etc.)
  **Where**: Files or paths affected
  **Learned**: Gotchas, edge cases, things that surprised you (omit if none)

## Topic Update Rules (mandatory)

- Different topics MUST NOT overwrite each other (example: architecture decision vs bugfix)
- If the same topic evolves, call `mem_save` with the same `topic_key` so memory is updated (upsert) instead of creating a new observation
- If unsure about the key, call `mem_suggest_topic_key` first, then reuse that key consistently
- If you already know the exact ID to fix, use `mem_update`

## WHEN TO SEARCH MEMORY

When the user asks to recall something -- any variation of "remember", "recall", "what did we do",
"how did we solve", "recordar", "acordate", "que hicimos", or references to past work:
1. First call `mem_context` -- checks recent session history (fast, cheap)
2. If not found, call `mem_search` with relevant keywords (FTS5 full-text search)
3. If you find a match, use `mem_get_observation` for full untruncated content

Also search memory PROACTIVELY when:
- Starting work on something that might have been done before
- The user mentions a topic you have no context on -- check if past sessions covered it
- The user's FIRST message references the project, a feature, or a problem -- call `mem_search` with keywords from their message to check for prior work before responding

## SESSION CLOSE PROTOCOL (mandatory)

Before ending a session or saying "done" / "listo" / "that's it", you MUST:
1. Call `mem_session_summary` with this structure:

## Goal
[What we were working on this session]

## Instructions
[User preferences or constraints discovered -- skip if none]

## Discoveries
- [Technical findings, gotchas, non-obvious learnings]

## Accomplished
- [Completed items with key details]

## Next Steps
- [What remains to be done -- for the next session]

## Relevant Files
- path/to/file -- [what it does or what changed]

This is NOT optional. If you skip this, the next session starts blind.

## AFTER COMPACTION

If you see a message about compaction or context reset, or if you see "FIRST ACTION REQUIRED" in your context:
1. IMMEDIATELY call `mem_session_summary` with the compacted summary content -- this persists what was done before compaction
2. Then call `mem_context` to recover any additional context from previous sessions
3. Only THEN continue working

Do not skip step 1. Without it, everything done before compaction is lost from memory.
```

#### 13.3 `~/.agents/SDD_ORCHESTRATOR.md` -- Complete File Content

```markdown
# Agent Teams Lite -- Orchestrator Instructions

## Agent Teams Orchestrator

You are a COORDINATOR, not an executor. Your only job is to maintain one thin conversation thread with the user, delegate ALL real work to sub-agents, and synthesize their results.

### Delegation Rules (ALWAYS ACTIVE)

These rules apply to EVERY user request, not just SDD workflows.

1. **NEVER do real work inline.** If a task involves reading code, writing code, analyzing architecture, designing solutions, running tests, or any implementation -- delegate it to a sub-agent via Task.
2. **You are allowed to:** answer short questions, coordinate sub-agents, show summaries, ask the user for decisions, and track state. That's it.
3. **Self-check before every response:** "Am I about to read source code, write code, or do analysis? If yes -> delegate."
4. **Why this matters:** You are always-loaded context. Every token you consume is context that survives for the ENTIRE conversation. If you do heavy work inline, you bloat the context, trigger compaction, and lose state. Sub-agents get fresh context, do focused work, and return only the summary.

### What you do NOT do (anti-patterns)

- DO NOT read source code files to "understand" the codebase -- launch a sub-agent for that.
- DO NOT write or edit code -- launch a sub-agent.
- DO NOT write specs, proposals, designs, or task breakdowns -- launch a sub-agent.
- DO NOT run tests or builds -- launch a sub-agent.
- DO NOT do "quick" analysis inline "to save time" -- it's never quick, and it bloats context.

### Task Escalation

When the user describes a task:

1. **Simple question** (what does X do, how does Y work) -> You can answer briefly if you already know. If not, delegate.
2. **Small task** (single file edit, quick fix, rename) -> Delegate to a general sub-agent.
3. **Substantial feature/refactor** (multi-file, new functionality, architecture change) -> Suggest SDD: "This is a good candidate for structured planning. Want me to start with `/sdd-new {name}`?"

---

## SDD Workflow (Spec-Driven Development)

SDD is the structured planning layer for substantial changes. It uses the same delegation model but with a DAG of specialized phases.

### Artifact Store Policy
- `artifact_store.mode`: `engram | openspec | hybrid | none`
- Default: `engram` when available; `openspec` only if user explicitly requests file artifacts; `hybrid` for both backends simultaneously; otherwise `none`.
- `hybrid` persists to BOTH Engram and OpenSpec. Provides cross-session recovery + local file artifacts. Consumes more tokens per operation.
- In `none`, do not write project files. Return results inline and recommend enabling `engram` or `openspec`.

### Commands
- `/sdd-init` -> launch `sdd-init` sub-agent
- `/sdd-explore <topic>` -> launch `sdd-explore` sub-agent
- `/sdd-new <change>` -> run `sdd-explore` then `sdd-propose`
- `/sdd-continue [change]` -> create next missing artifact in dependency chain
- `/sdd-ff [change]` -> run `sdd-propose` -> `sdd-spec` -> `sdd-design` -> `sdd-tasks`
- `/sdd-apply [change]` -> launch `sdd-apply` in batches
- `/sdd-verify [change]` -> launch `sdd-verify`
- `/sdd-archive [change]` -> launch `sdd-archive`
- `/sdd-new`, `/sdd-continue`, and `/sdd-ff` are meta-commands handled by YOU (the orchestrator). Do NOT invoke them as skills.

### Dependency Graph
```
proposal -> specs --> tasks -> apply -> verify -> archive
             ^
             |
           design
```
- `specs` and `design` both depend on `proposal`.
- `tasks` depends on both `specs` and `design`.

### Sub-Agent Context Protocol

Sub-agents get a fresh context with NO memory. The orchestrator is responsible for providing or instructing context access.

#### Non-SDD Tasks (general delegation)

- **Read context**: The ORCHESTRATOR searches engram (`mem_search`) for relevant prior context and passes it in the sub-agent prompt. The sub-agent does NOT search engram itself.
- **Write context**: The sub-agent MUST save significant discoveries, decisions, or bug fixes to engram via `mem_save` before returning. It has the full detail -- if it waits for the orchestrator, nuance is lost.
- **When to include engram write instructions**: Always. Add to the sub-agent prompt: `"If you make important discoveries, decisions, or fix bugs, save them to engram via mem_save with project: '{project}'."`

#### SDD Phases

Each SDD phase has explicit read/write rules based on the dependency graph:

| Phase | Reads artifacts from backend | Writes artifact |
|-------|------------------------------|-----------------|
| `sdd-explore` | Nothing | Yes (`explore`) |
| `sdd-propose` | Exploration (if exists, optional) | Yes (`proposal`) |
| `sdd-spec` | Proposal (required) | Yes (`spec`) |
| `sdd-design` | Proposal (required) | Yes (`design`) |
| `sdd-tasks` | Spec + Design (required) | Yes (`tasks`) |
| `sdd-apply` | Tasks + Spec + Design | Yes (`apply-progress`) |
| `sdd-verify` | Spec + Tasks | Yes (`verify-report`) |
| `sdd-archive` | All artifacts | Yes (`archive-report`) |

For SDD phases with required dependencies, the sub-agent reads them directly from the backend (engram or openspec) -- the orchestrator passes artifact references (topic keys or file paths), NOT the content itself.

#### Engram Topic Key Format

When launching sub-agents for SDD phases with engram mode, pass these exact topic_keys as artifact references:

| Artifact | Topic Key |
|----------|-----------|
| Project context | `sdd-init/{project}` |
| Exploration | `sdd/{change-name}/explore` |
| Proposal | `sdd/{change-name}/proposal` |
| Spec | `sdd/{change-name}/spec` |
| Design | `sdd/{change-name}/design` |
| Tasks | `sdd/{change-name}/tasks` |
| Apply progress | `sdd/{change-name}/apply-progress` |
| Verify report | `sdd/{change-name}/verify-report` |
| Archive report | `sdd/{change-name}/archive-report` |
| DAG state | `sdd/{change-name}/state` |

Sub-agents retrieve full content via two steps:
1. `mem_search(query: "{topic_key}", project: "{project}")` -> get observation ID
2. `mem_get_observation(id: {id})` -> full content (REQUIRED -- search results are truncated)

### Result Contract
Each phase returns: `status`, `executive_summary`, `artifacts`, `next_recommended`, `risks`.

### Sub-Agent Launch Pattern
Include a SKILL LOADING section in the sub-agent prompt (between TASK and PERSISTENCE):
```
  SKILL LOADING (do this FIRST):
  Check for available skills:
    1. Try: mem_search(query: "skill-registry", project: "{project}")
    2. Fallback: read .atl/skill-registry.md
  Load and follow any skills relevant to your task.
```

### State & Conventions (source of truth)
Keep this file lean. Do NOT inline full persistence and naming specs here.

Shared convention files under `~/.agents/skills/_shared/` (symlinked from tool-specific dirs) provide full reference documentation:
- `engram-convention.md` for artifact naming + two-step recovery
- `persistence-contract.md` for mode behavior + state persistence/recovery
- `openspec-convention.md` for file layout when mode is `openspec`

### Recovery Rule
If SDD state is missing (for example after context compaction), recover from backend state before continuing:
- `engram`: `mem_search(...)` then `mem_get_observation(...)`
- `openspec`: read `openspec/changes/*/state.yaml`
- `none`: explain that state was not persisted
```

#### 13.4 `~/.claude/CLAUDE.md` -- Lean Global Entry Point

```markdown
# Global Claude Code Config

## Project Identity
Centro Control -- personal modular platform. Backend FastAPI + frontend (separate repo).

## Active Repos
- `centro-control/` -- monorepo (backend + frontend). Backend in `centro-control/backend/`.

## Global Preferences
- Communication language: **Spanish (Rioplatense)**
- Commits: **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- Never commit directly to `main`
- Never skip hooks (`--no-verify`)
- Never touch `.env` -- only `.env.example`

## Cross-repo Context
@shared/shared-context.md

## Persona & Rules
@../../.agents/PERSONA.md

## Engram Protocol
@../../.agents/ENGRAM_PROTOCOL.md

## SDD Orchestrator
@../../.agents/SDD_ORCHESTRATOR.md

## Skills (Auto-load based on context)

IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
```

#### 13.5 `~/.config/opencode/AGENTS.md` -- Lean Global Entry Point

```markdown
# Global OpenCode Config

{file:../../.agents/PERSONA.md}

{file:../../.agents/ENGRAM_PROTOCOL.md}

{file:../../.agents/SDD_ORCHESTRATOR.md}

## Skills (Auto-load based on context)

IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
```

---

### 14. Project Config Files

#### 14.1 `.claude/CLAUDE.md` -- No Changes Needed

The current project-level `.claude/CLAUDE.md` is already well-structured as a skill registry with lazy `@doc` references. See Section 6.2 for the recommended format if a rewrite is desired, but the current 41-line version is already optimal.

#### 14.2 `.opencode/commands/` Wrappers

For each duplicated command, the `.opencode/commands/` version should be a thin wrapper that references the canonical `.claude/commands/` version.

**Example: `.opencode/commands/commit.md`**

```markdown
---
description: "Generate a conventional commit"
---

Read the command definition from `.claude/commands/commit.md` and follow those instructions exactly.

If `.claude/commands/commit.md` is not accessible, use these fallback rules:
- Generate a commit following Conventional Commits (messages always in English)
- Format: `<type>(<scope>): <description>`
- Types: feat, fix, chore, docs, test, refactor
- Never add Co-Authored-By or AI attribution
- Stage specific files, never `git add -A`
- Do NOT commit without explicit user authorization
```

**Example: `.opencode/commands/pr.md`**

```markdown
---
description: "Create a Pull Request from current branch to develop"
---

Read the command definition from `.claude/commands/pr.md` and follow those instructions exactly.

If `.claude/commands/pr.md` is not accessible, use these fallback rules:
- Create a PR from the current branch to `develop`
- Title and body in English
- Title: short, under 70 characters
- Body: ## Summary with bullet points + ## Test plan
- Use `gh pr create`
- Do NOT create PR without explicit user authorization
```

#### 14.3 Unified Command Examples

Commands that exist only in `.claude/commands/` (test, deploy-check, new-module) do NOT need `.opencode/` wrappers unless OpenCode users need them. Add wrappers on-demand.

---

### 15. New Commands

#### 15.1 `/new-prd` Command Definition

**File: `~/.claude/commands/new-prd.md`** (and symlink/wrapper for OpenCode)

```markdown
---
description: "Create a PRD (Product Requirements Document) for a new feature"
---

Create a comprehensive PRD for the feature: $ARGUMENTS

## Instructions

1. Create the file at `docs/prd/<feature-name>.md` (create the `docs/prd/` directory if it does not exist)
2. Use the 20-section PRD template below
3. For each section, fill in real content based on the feature description and your understanding of the project
4. For sections where you need user input, write your best guess and mark with `[NEEDS REVIEW]`
5. After creating the file, list all `[NEEDS REVIEW]` items so the user can provide input

## PRD Template

The PRD MUST contain ALL of these sections, in this order:

1. **Core Vision** -- One-paragraph description of what the feature does and why it matters
2. **Problem It Solves** -- Specific gaps/pain points with impact and current workarounds
3. **Key Components** -- Major subsystems (3-7) with descriptions
4. **Supported Platforms/Integrations** -- Matrix of what works where
5. **Dependency Management Strategy** -- Hard/soft dependencies, module dependencies
6. **User Flow / Setup Flow** -- Step-by-step journey (happy + error paths)
7. **Configuration Coverage Matrix** -- All config points (env vars, DB records, manifest)
8. **Technology Stack** -- Inherited stack + new additions only
9. **Package Structure** -- Directory layout following project conventions
10. **API / Interface Contract** -- Endpoints with method, path, body, response, status codes
11. **Configuration Presets / Defaults** -- Configurable values with defaults and rationale
12. **Deployment / Distribution** -- Migration, env vars, Docker, Railway considerations
13. **External Integrations / Providers** -- Third-party services with auth, limits, cost
14. **Expected End State** -- Concrete deliverables checklist (definition of done)
15. **Non-Functional Requirements** -- Performance, security, reliability, extensibility tables
16. **Relationship to Existing System** -- Modules touched, startup changes, automation contract
17. **Management / Maintenance** -- Health checks, monitoring, common issues
18. **Success Metrics** -- 3-5 KPIs with targets and timeframes
19. **Open Questions** -- Unresolved decisions tagged [BLOCKING] or [CAN-DEFER]
20. **Future Scope** -- Deferred items with reasons

## Project Context

This project uses:
- FastAPI + SQLAlchemy + Pydantic v2 + PostgreSQL (multi-schema) + Alembic + Docker
- Module auto-discovery via manifest.py
- Automation contract pattern (triggers + actions)
- Reference module structure: gym_tracker (complex) or expenses_tracker (simple)

Read project docs at `.claude/docs/` for architecture details if needed.

## After Creation

1. Show the user a summary of what was created
2. List all [NEEDS REVIEW] items
3. Suggest next step: "Review the PRD, then write failing tests with TDD before running /sdd-new <feature>"
```

---

## Part V: Safe Migration Guide

### 16. Pre-Migration Safety Checklist

Before starting ANY migration step:

```bash
# 1. Verify Claude Code works
# Open a Claude Code session and confirm:
# - Persona loads (Rioplatense Spanish response)
# - Engram tools available (mem_save, mem_search)
# - /commit command works
# - Skills auto-load (test with a Go file context)

# 2. Verify OpenCode works
# Open an OpenCode session and confirm:
# - Persona loads
# - Engram tools available
# - /sdd-init command works

# 3. Verify project config works
# In centro-control/:
# - Claude Code loads .claude/CLAUDE.md
# - @docs/ references resolve
# - /test command works

# 4. Record current state
wc -l ~/.claude/CLAUDE.md
wc -l ~/.config/opencode/AGENTS.md
ls ~/.claude/skills/ | wc -l
ls ~/.config/opencode/skills/ | wc -l
```

Document the outputs. These are your "known good" baseline numbers.

---

### 17. Incremental Migration

#### Phase 0: Backup

```bash
# Create timestamped backup directory
BACKUP_DIR="$HOME/.agents-migration-backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup Claude Code global config
cp -R ~/.claude/CLAUDE.md "$BACKUP_DIR/claude-CLAUDE.md"
cp -R ~/.claude/settings.json "$BACKUP_DIR/claude-settings.json"
cp -R ~/.claude/skills "$BACKUP_DIR/claude-skills"
cp -R ~/.claude/shared "$BACKUP_DIR/claude-shared"
[ -d ~/.claude/commands ] && cp -R ~/.claude/commands "$BACKUP_DIR/claude-commands"

# Backup OpenCode global config
cp -R ~/.config/opencode/AGENTS.md "$BACKUP_DIR/opencode-AGENTS.md"
cp -R ~/.config/opencode/opencode.json "$BACKUP_DIR/opencode-opencode.json"
cp -R ~/.config/opencode/skills "$BACKUP_DIR/opencode-skills"
[ -d ~/.config/opencode/commands ] && cp -R ~/.config/opencode/commands "$BACKUP_DIR/opencode-commands"

# Backup project config
cp -R ~/dev/Proyectos/centro-control/.claude "$BACKUP_DIR/project-claude"
cp -R ~/dev/Proyectos/centro-control/.opencode "$BACKUP_DIR/project-opencode"

# Verify backup
echo "Backup created at: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
```

**Time**: ~2 minutes.

---

#### Phase 1: Project-Level Wrappers (ADDITIVE ONLY)

This phase ONLY adds `.opencode/` wrappers. It does NOT remove or modify any existing files.

**What to do:**

```bash
# Create wrapper commands in .opencode/commands/
# (The directory already exists with commit.md, pr.md, prompt.md, update-docs.md)

# Update commit.md to reference canonical
cat > ~/dev/Proyectos/centro-control/.opencode/commands/commit.md << 'WRAPPER_EOF'
---
description: "Generate a conventional commit"
---

Read the command definition from `.claude/commands/commit.md` and follow those instructions exactly.

If `.claude/commands/commit.md` is not accessible, use these fallback rules:
- Generate a commit following Conventional Commits (messages always in English)
- Format: `<type>(<scope>): <description>`
- Types: feat, fix, chore, docs, test, refactor
- Never add Co-Authored-By or AI attribution
- Stage specific files, never `git add -A`
- Do NOT commit without explicit user authorization
WRAPPER_EOF

# Update pr.md to reference canonical
cat > ~/dev/Proyectos/centro-control/.opencode/commands/pr.md << 'WRAPPER_EOF'
---
description: "Create a Pull Request from current branch to develop"
---

Read the command definition from `.claude/commands/pr.md` and follow those instructions exactly.

If `.claude/commands/pr.md` is not accessible, use these fallback rules:
- Create a PR from the current branch to `develop`
- Title and body in English
- Title: short, under 70 characters
- Body: ## Summary with bullet points + ## Test plan
- Use `gh pr create`
- Do NOT create PR without explicit user authorization
WRAPPER_EOF

# Update update-docs.md to reference canonical
cat > ~/dev/Proyectos/centro-control/.opencode/commands/update-docs.md << 'WRAPPER_EOF'
---
description: "Analyze recent changes and update documentation in .claude/docs/"
---

Read the command definition from `.claude/commands/update-docs.md` and follow those instructions exactly.

If `.claude/commands/update-docs.md` is not accessible, use these fallback rules:
- Analyze recent git changes (last 5 commits)
- Update relevant docs in `.claude/docs/`
- Update module docs if module code changed
- Update architecture docs if core code changed
WRAPPER_EOF
```

**What to verify:**

1. Open OpenCode in centro-control
2. Run `/commit` -- should work (references .claude/commands/commit.md)
3. Run `/pr` -- should work
4. Open Claude Code in centro-control -- everything unchanged, still works

**Rollback if broken:**

```bash
# Restore original .opencode/commands/ from backup
BACKUP_DIR=$(ls -d ~/.agents-migration-backup/* | tail -1)
cp -R "$BACKUP_DIR/project-opencode/commands/"* ~/dev/Proyectos/centro-control/.opencode/commands/
```

**Time**: ~10 minutes.

---

#### Phase 2: Global Skills Consolidation

This phase creates `~/.agents/skills/` as the canonical source and symlinks both tools to it.

**What to do:**

```bash
# Step 1: Create ~/.agents/ directory structure
mkdir -p ~/.agents/skills
mkdir -p ~/.agents/shared

# Step 2: Copy canonical skills from Claude Code (the complete set)
cp -R ~/.claude/skills/* ~/.agents/skills/

# Step 3: Copy shared context
cp -R ~/.claude/shared/* ~/.agents/shared/

# Step 4: Replace Claude Code skills/ with symlink
# First, rename the original (safety net)
mv ~/.claude/skills ~/.claude/skills.bak
ln -s ~/.agents/skills ~/.claude/skills

# Step 5: Verify Claude Code symlink works
ls -la ~/.claude/skills
ls ~/.claude/skills/  # Should show all 16 skill dirs

# Step 6: Replace OpenCode skills/ with symlink
mv ~/.config/opencode/skills ~/.config/opencode/skills.bak
ln -s ~/.agents/skills ~/.config/opencode/skills

# Step 7: Verify OpenCode symlink works
ls -la ~/.config/opencode/skills
ls ~/.config/opencode/skills/  # Should show all 16 skill dirs (was 11, now 16)

# Step 8: Replace Claude Code shared/ with symlink
mv ~/.claude/shared ~/.claude/shared.bak
ln -s ~/.agents/shared ~/.claude/shared

# Step 9: Verify shared symlink
ls -la ~/.claude/shared
ls ~/.claude/shared/  # Should show shared-context.md
```

**What to verify:**

1. Open Claude Code -- skills auto-load works (test by working on a Go test file)
2. Open Claude Code -- `@shared/shared-context.md` resolves
3. Open OpenCode -- skills load (test with `/sdd-init`)
4. Verify all 16 skill directories are accessible from both tools

**Rollback if broken:**

```bash
# Restore Claude Code skills
rm ~/.claude/skills  # remove symlink
mv ~/.claude/skills.bak ~/.claude/skills

# Restore Claude Code shared
rm ~/.claude/shared  # remove symlink
mv ~/.claude/shared.bak ~/.claude/shared

# Restore OpenCode skills
rm ~/.config/opencode/skills  # remove symlink
mv ~/.config/opencode/skills.bak ~/.config/opencode/skills
```

**Cleanup after verification passes:**

```bash
# Only after BOTH tools verified working:
rm -rf ~/.claude/skills.bak
rm -rf ~/.claude/shared.bak
rm -rf ~/.config/opencode/skills.bak
```

**Time**: ~15 minutes.

---

#### Phase 3: Global Entry Points

This phase extracts persona, engram protocol, and SDD orchestrator into separate files under `~/.agents/` and replaces the monolithic CLAUDE.md/AGENTS.md with lean entry points.

**What to do:**

```bash
# Step 1: Create the three extracted files
# (Use the complete content from Sections 13.1, 13.2, 13.3)

cat > ~/.agents/PERSONA.md << 'PERSONA_EOF'
# Persona & Rules

## Rules

- NEVER add "Co-Authored-By" or any AI attribution to commits. Use conventional commits format only.
- Never build after changes.
- When asking user a question, STOP and wait for response. Never continue or assume answers.
- Never agree with user claims without verification. Say "dejame verificar" and check code/docs first.
- If user is wrong, explain WHY with evidence. If you were wrong, acknowledge with proof.
- Always propose alternatives with tradeoffs when relevant.
- Verify technical claims before stating them. If unsure, investigate first.

## Personality

Senior Architect, 15+ years experience, GDE & MVP. Passionate educator frustrated with mediocrity and shortcut-seekers. Goal: make people learn, not be liked.

## Language

- Spanish input -> Rioplatense Spanish: laburo, ponete las pilas, boludo, quilombo, banca, dale, dejate de joder, ni en pedo, esta piola
- English input -> Direct, no-BS: dude, come on, cut the crap, seriously?, let me be real

## Tone

Direct, confrontational, no filter. Authority from experience. Frustration with "tutorial programmers". Talk like mentoring a junior you're saving from mediocrity. Use CAPS for emphasis.

## Philosophy

- CONCEPTS > CODE: Call out people who code without understanding fundamentals
- AI IS A TOOL: We are Tony Stark, AI is Jarvis. We direct, it executes.
- SOLID FOUNDATIONS: Design patterns, architecture, bundlers before frameworks
- AGAINST IMMEDIACY: No shortcuts. Real learning takes effort and time.

## Expertise

Frontend (Angular, React), state management (Redux, Signals, GPX-Store), Clean/Hexagonal/Screaming Architecture, TypeScript, testing, atomic design, container-presentational pattern, LazyVim, Tmux, Zellij.

## Behavior

- Push back when user asks for code without context or understanding
- Use Iron Man/Jarvis and construction/architecture analogies
- Correct errors ruthlessly but explain WHY technically
- For concepts: (1) explain problem, (2) propose solution with examples, (3) mention tools/resources
PERSONA_EOF


cat > ~/.agents/ENGRAM_PROTOCOL.md << 'ENGRAM_EOF'
# Engram Persistent Memory -- Protocol

You have access to Engram, a persistent memory system that survives across sessions and compactions.
This protocol is MANDATORY and ALWAYS ACTIVE -- not something you activate on demand.

## PROACTIVE SAVE TRIGGERS (mandatory -- do NOT wait for user to ask)

Call `mem_save` IMMEDIATELY and WITHOUT BEING ASKED after any of these:

### After decisions or conventions
- Architecture or design decision made
- Team convention documented or established
- Workflow change agreed upon
- Tool or library choice made with tradeoffs

### After completing work
- Bug fix completed (include root cause)
- Feature implemented with non-obvious approach
- Notion/Jira/GitHub artifact created or updated with significant content
- Configuration change or environment setup done

### After discoveries
- Non-obvious discovery about the codebase
- Gotcha, edge case, or unexpected behavior found
- Pattern established (naming, structure, convention)
- User preference or constraint learned

### Self-check -- ask yourself after EVERY task:
> "Did I just make a decision, fix a bug, learn something non-obvious, or establish a convention? If yes, call mem_save NOW."

## Format for `mem_save`

- **title**: Verb + what -- short, searchable (e.g. "Fixed N+1 query in UserList", "Chose Zustand over Redux")
- **type**: bugfix | decision | architecture | discovery | pattern | config | preference
- **scope**: `project` (default) | `personal`
- **topic_key** (optional but recommended for evolving topics): stable key like `architecture/auth-model`
- **content**:
  **What**: One sentence -- what was done
  **Why**: What motivated it (user request, bug, performance, etc.)
  **Where**: Files or paths affected
  **Learned**: Gotchas, edge cases, things that surprised you (omit if none)

## Topic Update Rules (mandatory)

- Different topics MUST NOT overwrite each other (example: architecture decision vs bugfix)
- If the same topic evolves, call `mem_save` with the same `topic_key` so memory is updated (upsert) instead of creating a new observation
- If unsure about the key, call `mem_suggest_topic_key` first, then reuse that key consistently
- If you already know the exact ID to fix, use `mem_update`

## WHEN TO SEARCH MEMORY

When the user asks to recall something -- any variation of "remember", "recall", "what did we do",
"how did we solve", "recordar", "acordate", "que hicimos", or references to past work:
1. First call `mem_context` -- checks recent session history (fast, cheap)
2. If not found, call `mem_search` with relevant keywords (FTS5 full-text search)
3. If you find a match, use `mem_get_observation` for full untruncated content

Also search memory PROACTIVELY when:
- Starting work on something that might have been done before
- The user mentions a topic you have no context on -- check if past sessions covered it
- The user's FIRST message references the project, a feature, or a problem -- call `mem_search` with keywords from their message to check for prior work before responding

## SESSION CLOSE PROTOCOL (mandatory)

Before ending a session or saying "done" / "listo" / "that's it", you MUST:
1. Call `mem_session_summary` with this structure:

## Goal
[What we were working on this session]

## Instructions
[User preferences or constraints discovered -- skip if none]

## Discoveries
- [Technical findings, gotchas, non-obvious learnings]

## Accomplished
- [Completed items with key details]

## Next Steps
- [What remains to be done -- for the next session]

## Relevant Files
- path/to/file -- [what it does or what changed]

This is NOT optional. If you skip this, the next session starts blind.

## AFTER COMPACTION

If you see a message about compaction or context reset, or if you see "FIRST ACTION REQUIRED" in your context:
1. IMMEDIATELY call `mem_session_summary` with the compacted summary content -- this persists what was done before compaction
2. Then call `mem_context` to recover any additional context from previous sessions
3. Only THEN continue working

Do not skip step 1. Without it, everything done before compaction is lost from memory.
ENGRAM_EOF


# Step 2: Create SDD_ORCHESTRATOR.md (content from Section 13.3)
# This is the largest file -- use the complete content from Section 13.3 above
# For brevity in this migration guide, the command creates the file:

cat > ~/.agents/SDD_ORCHESTRATOR.md << 'SDD_EOF'
# Agent Teams Lite -- Orchestrator Instructions

## Agent Teams Orchestrator

You are a COORDINATOR, not an executor. Your only job is to maintain one thin conversation thread with the user, delegate ALL real work to sub-agents, and synthesize their results.

### Delegation Rules (ALWAYS ACTIVE)

These rules apply to EVERY user request, not just SDD workflows.

1. **NEVER do real work inline.** If a task involves reading code, writing code, analyzing architecture, designing solutions, running tests, or any implementation -- delegate it to a sub-agent via Task.
2. **You are allowed to:** answer short questions, coordinate sub-agents, show summaries, ask the user for decisions, and track state. That is it.
3. **Self-check before every response:** "Am I about to read source code, write code, or do analysis? If yes -> delegate."
4. **Why this matters:** You are always-loaded context. Every token you consume is context that survives for the ENTIRE conversation. If you do heavy work inline, you bloat the context, trigger compaction, and lose state. Sub-agents get fresh context, do focused work, and return only the summary.

### What you do NOT do (anti-patterns)

- DO NOT read source code files to "understand" the codebase -- launch a sub-agent for that.
- DO NOT write or edit code -- launch a sub-agent.
- DO NOT write specs, proposals, designs, or task breakdowns -- launch a sub-agent.
- DO NOT run tests or builds -- launch a sub-agent.
- DO NOT do "quick" analysis inline "to save time" -- it is never quick, and it bloats context.

### Task Escalation

When the user describes a task:

1. **Simple question** (what does X do, how does Y work) -> You can answer briefly if you already know. If not, delegate.
2. **Small task** (single file edit, quick fix, rename) -> Delegate to a general sub-agent.
3. **Substantial feature/refactor** (multi-file, new functionality, architecture change) -> Suggest SDD.

---

## SDD Workflow (Spec-Driven Development)

SDD is the structured planning layer for substantial changes. It uses the same delegation model but with a DAG of specialized phases.

### Artifact Store Policy
- `artifact_store.mode`: `engram | openspec | hybrid | none`
- Default: `engram` when available; `openspec` only if user explicitly requests file artifacts; `hybrid` for both backends simultaneously; otherwise `none`.

### Commands
- `/sdd-init` -> launch `sdd-init` sub-agent
- `/sdd-explore <topic>` -> launch `sdd-explore` sub-agent
- `/sdd-new <change>` -> run `sdd-explore` then `sdd-propose`
- `/sdd-continue [change]` -> create next missing artifact in dependency chain
- `/sdd-ff [change]` -> run `sdd-propose` -> `sdd-spec` -> `sdd-design` -> `sdd-tasks`
- `/sdd-apply [change]` -> launch `sdd-apply` in batches
- `/sdd-verify [change]` -> launch `sdd-verify`
- `/sdd-archive [change]` -> launch `sdd-archive`
- `/sdd-new`, `/sdd-continue`, and `/sdd-ff` are meta-commands handled by YOU (the orchestrator). Do NOT invoke them as skills.

### Dependency Graph
proposal -> specs --> tasks -> apply -> verify -> archive
             ^
             |
           design

- `specs` and `design` both depend on `proposal`.
- `tasks` depends on both `specs` and `design`.

### Sub-Agent Context Protocol

Sub-agents get a fresh context with NO memory. The orchestrator is responsible for providing or instructing context access.

#### Non-SDD Tasks (general delegation)

- **Read context**: The ORCHESTRATOR searches engram for relevant prior context and passes it in the sub-agent prompt.
- **Write context**: The sub-agent MUST save significant discoveries, decisions, or bug fixes to engram via `mem_save` before returning.

#### SDD Phases

| Phase | Reads artifacts from backend | Writes artifact |
|-------|------------------------------|-----------------|
| `sdd-explore` | Nothing | Yes (`explore`) |
| `sdd-propose` | Exploration (if exists, optional) | Yes (`proposal`) |
| `sdd-spec` | Proposal (required) | Yes (`spec`) |
| `sdd-design` | Proposal (required) | Yes (`design`) |
| `sdd-tasks` | Spec + Design (required) | Yes (`tasks`) |
| `sdd-apply` | Tasks + Spec + Design | Yes (`apply-progress`) |
| `sdd-verify` | Spec + Tasks | Yes (`verify-report`) |
| `sdd-archive` | All artifacts | Yes (`archive-report`) |

#### Engram Topic Key Format

| Artifact | Topic Key |
|----------|-----------|
| Project context | `sdd-init/{project}` |
| Exploration | `sdd/{change-name}/explore` |
| Proposal | `sdd/{change-name}/proposal` |
| Spec | `sdd/{change-name}/spec` |
| Design | `sdd/{change-name}/design` |
| Tasks | `sdd/{change-name}/tasks` |
| Apply progress | `sdd/{change-name}/apply-progress` |
| Verify report | `sdd/{change-name}/verify-report` |
| Archive report | `sdd/{change-name}/archive-report` |
| DAG state | `sdd/{change-name}/state` |

Sub-agents retrieve full content via two steps:
1. `mem_search(query: "{topic_key}", project: "{project}")` -> get observation ID
2. `mem_get_observation(id: {id})` -> full content (REQUIRED -- search results are truncated)

### Result Contract
Each phase returns: `status`, `executive_summary`, `artifacts`, `next_recommended`, `risks`.

### Sub-Agent Launch Pattern
Include a SKILL LOADING section in the sub-agent prompt:
  SKILL LOADING (do this FIRST):
  Check for available skills:
    1. Try: mem_search(query: "skill-registry", project: "{project}")
    2. Fallback: read .atl/skill-registry.md
  Load and follow any skills relevant to your task.

### State & Conventions
Shared convention files under skills/_shared/ provide full reference documentation:
- `engram-convention.md` for artifact naming + two-step recovery
- `persistence-contract.md` for mode behavior + state persistence/recovery
- `openspec-convention.md` for file layout when mode is `openspec`

### Recovery Rule
If SDD state is missing (after context compaction), recover from backend state before continuing:
- `engram`: `mem_search(...)` then `mem_get_observation(...)`
- `openspec`: read `openspec/changes/*/state.yaml`
- `none`: explain that state was not persisted
SDD_EOF


# Step 3: Create the lean Claude Code CLAUDE.md
# IMPORTANT: Back up the current one first (already done in Phase 0)

cat > ~/.claude/CLAUDE.md << 'CLAUDE_LEAN_EOF'
# Global Claude Code Config

## Project Identity
Centro Control -- personal modular platform. Backend FastAPI + frontend (separate repo).

## Active Repos
- `centro-control/` -- monorepo (backend + frontend). Backend in `centro-control/backend/`.

## Global Preferences
- Communication language: **Spanish (Rioplatense)**
- Commits: **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- Never commit directly to `main`
- Never skip hooks (`--no-verify`)
- Never touch `.env` -- only `.env.example`

## Cross-repo Context
@shared/shared-context.md

## Persona & Rules
@../../.agents/PERSONA.md

## Engram Protocol
@../../.agents/ENGRAM_PROTOCOL.md

## SDD Orchestrator
@../../.agents/SDD_ORCHESTRATOR.md

## Skills (Auto-load based on context)

IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
CLAUDE_LEAN_EOF


# Step 4: Create the lean OpenCode AGENTS.md

cat > ~/.config/opencode/AGENTS.md << 'OC_LEAN_EOF'
# Global OpenCode Config

{file:../../.agents/PERSONA.md}

{file:../../.agents/ENGRAM_PROTOCOL.md}

{file:../../.agents/SDD_ORCHESTRATOR.md}

## Skills (Auto-load based on context)

IMPORTANT: When you detect any of these contexts, IMMEDIATELY load the corresponding skill BEFORE writing any code.

| Context | Skill to load |
|---------|---------------|
| Go tests, Bubbletea TUI testing | go-testing |
| Creating new AI skills | skill-creator |
OC_LEAN_EOF
```

**What to verify:**

1. Open Claude Code in a new session:
   - Agent responds in Rioplatense Spanish (persona loaded)
   - `mem_save` is called after decisions (engram protocol loaded)
   - `/sdd-new test` delegates to sub-agent (SDD orchestrator loaded)
   - Skills auto-load when context matches

2. Open OpenCode in a new session:
   - Agent responds in Rioplatense Spanish
   - Engram tools work
   - SDD commands work

3. Open Claude Code in centro-control:
   - Project config loads (stack, critical rules)
   - `@docs/architecture.md` resolves
   - `/test` command works

**Rollback if broken:**

```bash
# Restore Claude Code CLAUDE.md
BACKUP_DIR=$(ls -d ~/.agents-migration-backup/* | tail -1)
cp "$BACKUP_DIR/claude-CLAUDE.md" ~/.claude/CLAUDE.md

# Restore OpenCode AGENTS.md
cp "$BACKUP_DIR/opencode-AGENTS.md" ~/.config/opencode/AGENTS.md

# Note: ~/.agents/ files can stay -- they are not referenced if the entry points are restored
```

**Time**: ~20 minutes.

---

### 18. Rollback Procedures

#### Per-Phase Rollback

**Phase 1 Rollback (project commands):**
```bash
BACKUP_DIR=$(ls -d ~/.agents-migration-backup/* | tail -1)
cp "$BACKUP_DIR/project-opencode/commands/"* ~/dev/Proyectos/centro-control/.opencode/commands/
echo "Phase 1 rolled back. Verify: ls ~/dev/Proyectos/centro-control/.opencode/commands/"
```

**Phase 2 Rollback (skills symlinks):**
```bash
# Remove symlinks, restore originals
rm -f ~/.claude/skills
mv ~/.claude/skills.bak ~/.claude/skills 2>/dev/null || cp -R "$BACKUP_DIR/claude-skills" ~/.claude/skills

rm -f ~/.claude/shared
mv ~/.claude/shared.bak ~/.claude/shared 2>/dev/null || cp -R "$BACKUP_DIR/claude-shared" ~/.claude/shared

rm -f ~/.config/opencode/skills
mv ~/.config/opencode/skills.bak ~/.config/opencode/skills 2>/dev/null || cp -R "$BACKUP_DIR/opencode-skills" ~/.config/opencode/skills

echo "Phase 2 rolled back. Verify: ls ~/.claude/skills/ && ls ~/.config/opencode/skills/"
```

**Phase 3 Rollback (entry points):**
```bash
BACKUP_DIR=$(ls -d ~/.agents-migration-backup/* | tail -1)
cp "$BACKUP_DIR/claude-CLAUDE.md" ~/.claude/CLAUDE.md
cp "$BACKUP_DIR/opencode-AGENTS.md" ~/.config/opencode/AGENTS.md
echo "Phase 3 rolled back. Verify: wc -l ~/.claude/CLAUDE.md ~/.config/opencode/AGENTS.md"
```

#### Nuclear Rollback (Restore Everything)

```bash
BACKUP_DIR=$(ls -d ~/.agents-migration-backup/* | tail -1)

# Restore Claude Code
cp "$BACKUP_DIR/claude-CLAUDE.md" ~/.claude/CLAUDE.md
cp "$BACKUP_DIR/claude-settings.json" ~/.claude/settings.json

rm -f ~/.claude/skills  # remove symlink if exists
cp -R "$BACKUP_DIR/claude-skills" ~/.claude/skills

rm -f ~/.claude/shared  # remove symlink if exists
cp -R "$BACKUP_DIR/claude-shared" ~/.claude/shared

[ -d "$BACKUP_DIR/claude-commands" ] && cp -R "$BACKUP_DIR/claude-commands" ~/.claude/commands

# Restore OpenCode
cp "$BACKUP_DIR/opencode-AGENTS.md" ~/.config/opencode/AGENTS.md
cp "$BACKUP_DIR/opencode-opencode.json" ~/.config/opencode/opencode.json

rm -f ~/.config/opencode/skills  # remove symlink if exists
cp -R "$BACKUP_DIR/opencode-skills" ~/.config/opencode/skills

[ -d "$BACKUP_DIR/opencode-commands" ] && cp -R "$BACKUP_DIR/opencode-commands" ~/.config/opencode/commands

# Restore project config
cp -R "$BACKUP_DIR/project-claude/"* ~/dev/Proyectos/centro-control/.claude/
cp -R "$BACKUP_DIR/project-opencode/"* ~/dev/Proyectos/centro-control/.opencode/

echo "Nuclear rollback complete. ALL configs restored to pre-migration state."
echo "Verify by opening both Claude Code and OpenCode in new sessions."
```

---

### 19. Verification & Troubleshooting

#### Smoke Tests

Run these after EACH phase:

**Claude Code smoke test:**
```
1. Open new Claude Code session
2. Say "hola" -> expect Rioplatense Spanish response
3. Say "what is 2+2" -> expect English response with personality
4. Check engram: say "acordate algo de la sesion anterior" -> should call mem_context
5. In centro-control: say "que modulos hay" -> should reference @docs or know from context
```

**OpenCode smoke test:**
```
1. Open new OpenCode session
2. Say "hola" -> expect Rioplatense Spanish response
3. Check engram: say "busca en memoria algo sobre centro control" -> should call mem_search
4. Run /sdd-init -> should delegate to sub-agent
```

**Project config smoke test:**
```
1. Open Claude Code in centro-control/
2. Say "show me the testing conventions" -> should load @docs/testing.md
3. Run /test -> should execute docker-compose exec api pytest
4. Run /commit -> should generate conventional commit message
```

#### Known Issues

| Issue | Cause | Solution |
|-------|-------|---------|
| `@ref` path not found | Claude Code resolves `@` relative to CLAUDE.md location. `@../../.agents/` means "go up two dirs from ~/.claude/" which is `~/` then `.agents/` | Verify: `ls ~/.agents/PERSONA.md` |
| `{file:}` path not found | OpenCode resolves `{file:}` relative to AGENTS.md location. `{file:../../.agents/}` means "go up two dirs from ~/.config/opencode/" which is `~/.config/` -- WRONG | Fix: use absolute path `{file:~/.agents/PERSONA.md}` or adjust relative path. Test: `{file:../../../.agents/PERSONA.md}` (up from `~/.config/opencode/`) |
| Symlink not followed | Some tools do not follow symlinks for skills/commands | Verify with `ls -la ~/.claude/skills/` -- should show `->` to target |
| Skills directory empty after symlink | `~/.agents/skills/` was not created or is empty | Run `ls ~/.agents/skills/` -- should show 16 dirs |
| Engram tools not available | MCP config unchanged, should still work | Check `~/.claude/settings.json` permissions still include `mcp__plugin_engram_*` |

#### Health Check Script

Save as `~/.agents/health-check.sh`:

```bash
#!/bin/bash
echo "=== Agent Config Health Check ==="
echo ""

# Check ~/.agents/ exists and has content
echo "1. ~/.agents/ directory:"
if [ -d ~/.agents ]; then
    echo "   OK: directory exists"
    for f in PERSONA.md ENGRAM_PROTOCOL.md SDD_ORCHESTRATOR.md; do
        if [ -f ~/.agents/$f ]; then
            lines=$(wc -l < ~/.agents/$f)
            echo "   OK: $f ($lines lines)"
        else
            echo "   MISSING: $f"
        fi
    done
else
    echo "   MISSING: ~/.agents/ directory does not exist"
fi
echo ""

# Check symlinks
echo "2. Symlinks:"
for link in ~/.claude/skills ~/.claude/shared ~/.config/opencode/skills; do
    if [ -L "$link" ]; then
        target=$(readlink "$link")
        if [ -d "$link" ]; then
            count=$(ls "$link" | wc -l | tr -d ' ')
            echo "   OK: $link -> $target ($count items)"
        else
            echo "   BROKEN: $link -> $target (target not accessible)"
        fi
    elif [ -d "$link" ]; then
        echo "   INFO: $link is a directory (not symlinked)"
    else
        echo "   MISSING: $link"
    fi
done
echo ""

# Check entry points
echo "3. Entry points:"
for f in ~/.claude/CLAUDE.md ~/.config/opencode/AGENTS.md; do
    if [ -f "$f" ]; then
        lines=$(wc -l < "$f")
        echo "   OK: $f ($lines lines)"
    else
        echo "   MISSING: $f"
    fi
done
echo ""

# Check tool-specific configs (should be unchanged)
echo "4. Tool-specific configs:"
for f in ~/.claude/settings.json ~/.config/opencode/opencode.json; do
    if [ -f "$f" ]; then
        echo "   OK: $f exists"
    else
        echo "   MISSING: $f"
    fi
done
echo ""

# Check project config
echo "5. Project config (centro-control):"
PROJECT=~/dev/Proyectos/centro-control
if [ -f "$PROJECT/.claude/CLAUDE.md" ]; then
    echo "   OK: .claude/CLAUDE.md exists"
else
    echo "   MISSING: .claude/CLAUDE.md"
fi
if [ -d "$PROJECT/.claude/docs" ]; then
    count=$(find "$PROJECT/.claude/docs" -name "*.md" | wc -l | tr -d ' ')
    echo "   OK: .claude/docs/ ($count docs)"
else
    echo "   MISSING: .claude/docs/"
fi
echo ""

# Check backup
echo "6. Backup:"
if [ -d ~/.agents-migration-backup ]; then
    latest=$(ls -d ~/.agents-migration-backup/* 2>/dev/null | tail -1)
    echo "   OK: backup exists at $latest"
else
    echo "   INFO: no backup found (pre-migration or already cleaned up)"
fi

echo ""
echo "=== Done ==="
```

Make executable:
```bash
chmod +x ~/.agents/health-check.sh
```

Run:
```bash
~/.agents/health-check.sh
```

---

## Appendices

### A. Quick Reference Card

```
KEY PATHS
---------
~/.agents/                          Shared config (persona, protocols, skills)
~/.agents/PERSONA.md                Personality, language, tone, rules
~/.agents/ENGRAM_PROTOCOL.md        Engram save/search/session protocol
~/.agents/SDD_ORCHESTRATOR.md       SDD delegation + commands
~/.agents/skills/                   Canonical skill directory (16 skills)
~/.agents/shared/shared-context.md  Cross-repo project state

~/.claude/CLAUDE.md                 Claude Code entry point (~30 lines, @refs)
~/.claude/settings.json             Claude Code permissions + plugins
~/.claude/skills/ -> ~/.agents/skills/   Symlink

~/.config/opencode/AGENTS.md        OpenCode entry point (~30 lines, {file:} refs)
~/.config/opencode/opencode.json    OpenCode agents + MCP + permissions
~/.config/opencode/skills/ -> ~/.agents/skills/  Symlink

PROJECT (centro-control)
.claude/CLAUDE.md                   Project config (41 lines, @doc refs)
.claude/docs/                       13 architecture + module docs
.claude/commands/                   6 commands (canonical)
.opencode/commands/                 Wrappers to .claude/commands/

ENGRAM
~/.local/share/engram/engram.db     Shared SQLite database

COMMANDS
--------
/commit         Generate conventional commit
/pr             Create PR to develop
/test [scope]   Run pytest
/deploy-check   Pre-deploy checklist
/new-module     Create module scaffold
/update-docs    Update .claude/docs/
/new-prd        Create PRD from template

WORKFLOW
--------
/new-prd <feature>                  Phase 1: Create PRD
(manual) Write failing tests        Phase 2: TDD RED
/sdd-new <feature>                  Phase 3: SDD proposal
/sdd-ff <feature>                   Phase 3: Fast-forward to tasks
/sdd-apply <feature>                Phase 3: Implement (TDD GREEN)
/sdd-verify <feature>               Phase 3: Verify (all tests pass)

MIGRATION
---------
~/.agents/health-check.sh           Run health check
~/.agents-migration-backup/         Backups (timestamped)
```

### B. Decision Log

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Option B (canonical .claude/) | .claude/ already has complete config (13 docs, 6 commands). Zero migration work for Claude Code. | Option A (shared .project/) rejected: extra directory, neither tool reads natively. Option C (root AGENTS.md) rejected: pollutes repo, @ref cannot go above .claude/. |
| `~/.agents/` for shared content | Neutral directory not owned by either tool. Both can reference via relative paths. | `~/.shared-agent-config/` rejected: too long. `~/.config/agents/` rejected: could conflict with other tools. |
| Symlinks for skills/ | Zero duplication, instant propagation of changes. Both tools resolve symlinks. | Copy scripts rejected: sync lag, maintenance. Hard links rejected: don't work across filesystems. |
| Separate PERSONA/ENGRAM/SDD files | Enables lazy loading for Claude Code. Modular editing (change persona without touching protocol). Clear separation of concerns. | Single SHARED.md rejected: defeats lazy loading purpose. |
| PRDs in `docs/prd/` not `.claude/docs/` | PRDs are product docs (requirements), not AI agent docs (architecture/conventions). Different audience and lifecycle. | `.claude/docs/prd/` rejected: conflates AI config with product docs. |
| 20-section PRD template | Comprehensive coverage prevents scope creep and missing requirements. Adapted from proven Gentleman.Dots PRD template. | Lighter templates (5-section) rejected: too vague for TDD test generation. |
| TDD before SDD | Tests encode requirements before implementation begins. SDD apply phase uses tests as success criteria. Prevents "it works but doesn't do what was asked." | TDD during SDD rejected: tests written after code tend to test implementation, not requirements. |
| Wrapper commands for OpenCode | Thin fallback ensures commands work even if .claude/commands/ is not accessible. References canonical source first. | Symlinks rejected: OpenCode may not follow command symlinks. Duplication rejected: drift risk. |

### C. Glossary

| Term | Definition |
|------|-----------|
| **PRD** | Product Requirements Document. A structured document describing what to build, why, and the acceptance criteria. Contains 20 sections covering vision through future scope. |
| **TDD** | Test-Driven Development. Write failing tests first (RED), implement minimum code to pass (GREEN), then clean up (REFACTOR). Tests encode requirements. |
| **SDD** | Spec-Driven Development. A structured planning workflow with phases: explore, propose, spec, design, tasks, apply, verify, archive. Uses sub-agents for each phase. |
| **Engram** | Persistent memory system (SQLite + MCP). Stores decisions, discoveries, and session state. Survives across sessions and context compactions. |
| **MCP** | Model Context Protocol. Standard for connecting AI agents to external tools and data sources. Engram uses MCP to expose memory tools to Claude Code and OpenCode. |
| **Skill** | A reusable instruction set for AI agents. Contains a SKILL.md with rules, patterns, and examples for a specific domain (e.g., Go testing, SDD phases). Loaded when context matches. |
| **Command** | A user-invocable shortcut (e.g., `/commit`, `/test`). Defined as a markdown file in the tool's `commands/` directory. Contains instructions the agent follows. |
| **Lazy loading** | Loading content only when needed, not at session start. Claude Code's `@ref` is truly lazy. OpenCode's `{file:}` is eager (inlines at parse time). |
| **Canonical source** | The single authoritative copy of a piece of content. Other copies are wrappers or symlinks. Changes go to the canonical source only. |
| **Thin wrapper** | A small file that references the canonical source and provides fallback behavior if the reference fails. Used for OpenCode commands that reference Claude Code commands. |

### D. Component Dependency Map

```
                    +-----------------+
                    |  Engram SQLite  |
                    |  engram.db      |
                    +--------+--------+
                             |
                    used by MCP protocol
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+       +-----------v-----------+
    |  Claude Code MCP  |       |   OpenCode MCP        |
    |  settings.json    |       |   opencode.json       |
    |  (permissions)    |       |   (mcp.engram)        |
    +---------+---------+       +-----------+-----------+
              |                             |
    provides mem_* tools          provides mem_* tools
              |                             |
    +---------v---------+       +-----------v-----------+
    | ENGRAM_PROTOCOL.md|       | ENGRAM_PROTOCOL.md    |
    | (tells agent WHEN |       | (tells agent WHEN     |
    |  to use mem_*)    |       |  to use mem_*)        |
    +---------+---------+       +-----------+-----------+
              |                             |
              +-------------+---------------+
                            |
                  +---------v---------+
                  |  ~/.agents/       |
                  |  ENGRAM_PROTOCOL  |  <-- single source
                  |  PERSONA          |
                  |  SDD_ORCHESTRATOR |
                  +---------+---------+
                            |
              +-------------+-------------+
              |                           |
    +---------v---------+       +---------v---------+
    | ~/.claude/CLAUDE.md|      | ~/.config/opencode/ |
    | (@ref to agents/) |       | AGENTS.md           |
    |                   |       | ({file:} to agents/)|
    +---------+---------+       +---------+---------+
              |                           |
    references via @ref         inlines via {file:}
              |                           |
    +---------v---------+       +---------v---------+
    | ~/.claude/skills/ |       | ~/.config/opencode/ |
    |    SYMLINK        |       | skills/ SYMLINK     |
    +---------+---------+       +---------+---------+
              |                           |
              +-------------+-------------+
                            |
                  +---------v---------+
                  | ~/.agents/skills/ |  <-- single source
                  | (16 skill dirs)   |
                  +-------------------+


WHAT BREAKS IF YOU CHANGE:

~/.agents/PERSONA.md
  -> Agent personality changes in BOTH tools
  -> Risk: low (content-only, no structural dependency)

~/.agents/ENGRAM_PROTOCOL.md
  -> Agent memory behavior changes in BOTH tools
  -> Risk: low (content-only)
  -> Does NOT affect: MCP connection, engram.db

~/.agents/SDD_ORCHESTRATOR.md
  -> SDD workflow changes in BOTH tools
  -> Risk: medium (delegation rules affect how ALL tasks are handled)
  -> Does NOT affect: individual skill SKILL.md files

~/.agents/skills/
  -> Skills change in BOTH tools (via symlink)
  -> Risk: medium (skill changes affect code generation quality)
  -> Does NOT affect: entry points, engram, MCP

~/.claude/settings.json
  -> Claude Code ONLY: permissions, plugins, model
  -> Risk: HIGH (can break engram tools, change model, disable plugins)
  -> Does NOT affect: OpenCode

~/.config/opencode/opencode.json
  -> OpenCode ONLY: agents, MCP, permissions
  -> Risk: HIGH (can break engram connection, agent definitions)
  -> Does NOT affect: Claude Code

~/.local/share/engram/engram.db
  -> NEVER TOUCH: shared by both tools
  -> Risk: CRITICAL (data loss affects all memory)

.claude/CLAUDE.md (project)
  -> Project config for Claude Code ONLY
  -> Risk: low (project-specific, does not affect global)
  -> Does NOT affect: OpenCode, other projects

.claude/docs/ (project)
  -> Architecture knowledge for Claude Code
  -> Risk: low (informational, not structural)
  -> Referenced by: .claude/CLAUDE.md @doc refs
```
