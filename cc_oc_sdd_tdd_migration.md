# Guía de Migración: Unificación de Configuración Claude Code + OpenCode

## TL;DR

Tenés configuración duplicada entre Claude Code y OpenCode. Esta guía te lleva a una arquitectura donde:
- **`~/.agents/`** es la ÚNICA FUENTE DE VERDAD para config compartida
- Symlinks eliminan duplicación
- Context window se optimiza con lazy loading
- Cambiar entre herramientas es transparente (misma memoria, mismos skills)

---

## 1. Executive Summary

### El Problema Actual

```
DUPLICACIÓN MASIVA:
├── ~/.claude/CLAUDE.md           → 322 líneas (persona + engram + SDD inline)
├── ~/.config/opencode/AGENTS.md  → 192 líneas (MISMA persona + SDD duplicado)
├── ~/.claude/skills/             → 16 skills
├── ~/.config/opencode/skills/    → 12 skills (DUPLICADOS)
└── ~/.claude/skills/_shared/     → 3 archivos (DUPLICADOS en opencode)

RESULTADO:
- Drift inevitable entre configs
- Mantenimiento doble
- Context window desperdiciado (322 líneas cargadas SIEMPRE)
- Bugs diferentes en cada herramienta
```

### La Arquitectura Target

```
SINGLE SOURCE OF TRUTH:
~/.agents/                        → TODO lo compartido vive acá
├── PERSONA.md                    → Personalidad (cargado bajo demanda)
├── ENGRAM_PROTOCOL.md            → Protocolo de memoria
├── SDD_ORCHESTRATOR.md           → Workflow SDD
├── skills/                       → TODOS los skills
└── commands/                     → Comandos universales

ENTRY POINTS (lean, < 50 líneas cada uno):
├── ~/.claude/CLAUDE.md           → Solo imports + reglas específicas
└── ~/.config/opencode/AGENTS.md  → Solo imports + reglas específicas

SYMLINKS (zero duplicación):
├── ~/.claude/skills              → ~/.agents/skills
└── ~/.config/opencode/skills     → ~/.agents/skills
```

### Beneficios

| Antes | Después |
|-------|---------|
| 322 líneas cargadas siempre | ~30 líneas + lazy loading |
| 2 configs para mantener | 1 source of truth |
| Skills duplicados | Symlinks, 0 duplicación |
| Drift entre herramientas | Imposible, misma fuente |
| Memoria separada | Ya unificada (engram) |

---

## 2. Arquitectura (Diagrama)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ~/.agents/                                        │
│                     (SINGLE SOURCE OF TRUTH)                                │
│                                                                             │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐              │
│  │ PERSONA.md  │  │ ENGRAM_PROTOCOL  │  │ SDD_ORCHESTRATOR  │              │
│  │ (50 líneas) │  │ (80 líneas)      │  │ (150 líneas)      │              │
│  └─────────────┘  └──────────────────┘  └───────────────────┘              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ skills/                                                              │   │
│  │ ├── _shared/         (conventions)                                   │   │
│  │ ├── sdd-*/           (SDD suite: 9 skills)                          │   │
│  │ ├── go-testing/      (Go patterns)                                   │   │
│  │ ├── skill-creator/   (crear skills)                                  │   │
│  │ ├── create-issue/    (GitHub issues)                                 │   │
│  │ ├── deploy-ios/      (Capacitor iOS)                                 │   │
│  │ └── ...              (resto de skills)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ commands/                                                            │   │
│  │ ├── commit.md        (universal)                                     │   │
│  │ ├── pr.md            (universal)                                     │   │
│  │ └── prompt.md        (universal)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                           │
          │ symlink                                   │ symlink
          ▼                                           ▼
┌─────────────────────────┐             ┌─────────────────────────────────┐
│ ~/.claude/              │             │ ~/.config/opencode/             │
│                         │             │                                 │
│ CLAUDE.md (~30 líneas)  │             │ AGENTS.md (~30 líneas)          │
│ ├── @PERSONA.md         │             │ ├── imports PERSONA.md          │
│ ├── @ENGRAM_PROTOCOL    │             │ ├── imports ENGRAM_PROTOCOL     │
│ └── @SDD_ORCHESTRATOR   │             │ └── imports SDD_ORCHESTRATOR    │
│                         │             │                                 │
│ skills/ ─────────────────────────────────────────────► ~/.agents/skills │
│ commands/ ───────────────────────────────────────────► ~/.agents/commands
│                         │             │                                 │
│ mcp/                    │             │ opencode.json                   │
│ └── engram.json         │             │ ├── MCP config                  │
│ └── context7.json       │             │ ├── sub-agents                  │
│                         │             │ └── permissions                 │
│ settings.json           │             │                                 │
└─────────────────────────┘             │ plugins/                        │
                                        │ └── engram.ts                   │
                                        └─────────────────────────────────┘
          │                                           │
          │ project-level                             │ project-level
          ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ <project>/.claude/                    <project>/.opencode/                  │
│                                                                             │
│ CLAUDE.md (project context)           commands/ (project-specific)          │
│ commands/ (project-specific)                                                │
│ docs/ (project documentation)                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              ENGRAM (SHARED)                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SQLite Database: ~/.local/share/engram/engram.db                   │   │
│  │  - Misma DB para Claude Code y OpenCode                             │   │
│  │  - MCP Server (Go binary) accedido por ambos                        │   │
│  │  - Memoria compartida = contexto compartido                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Estructura de Directorios (Target State)

```
~/.agents/                              # SINGLE SOURCE OF TRUTH
├── PERSONA.md                          # Personalidad, idioma, tono
├── ENGRAM_PROTOCOL.md                  # Protocolo de memoria persistente
├── SDD_ORCHESTRATOR.md                 # Workflow SDD completo
├── skills/                             # TODOS los skills compartidos
│   ├── _shared/                        # Convenciones
│   │   ├── engram-convention.md
│   │   ├── openspec-convention.md
│   │   └── persistence-contract.md
│   ├── sdd-init/
│   │   └── SKILL.md
│   ├── sdd-explore/
│   │   └── SKILL.md
│   ├── sdd-propose/
│   │   └── SKILL.md
│   ├── sdd-spec/
│   │   └── SKILL.md
│   ├── sdd-design/
│   │   └── SKILL.md
│   ├── sdd-tasks/
│   │   └── SKILL.md
│   ├── sdd-apply/
│   │   └── SKILL.md
│   ├── sdd-verify/
│   │   └── SKILL.md
│   ├── sdd-archive/
│   │   └── SKILL.md
│   ├── go-testing/
│   │   └── SKILL.md
│   ├── skill-creator/
│   │   └── SKILL.md
│   ├── create-issue/
│   │   └── SKILL.md
│   ├── deploy-ios/
│   │   └── SKILL.md
│   ├── find-skills/
│   │   └── SKILL.md
│   └── frontend-ui-ux-engineer/
│       └── SKILL.md
├── commands/                           # Comandos universales
│   ├── commit.md
│   ├── pr.md
│   └── prompt.md
└── .skill-lock.json                    # Tracking de skills instalados

~/.claude/                              # Claude Code entry point
├── CLAUDE.md                           # LEAN: ~30 líneas, solo imports
├── skills -> ~/.agents/skills          # SYMLINK
├── commands -> ~/.agents/commands      # SYMLINK (shared commands)
├── mcp/                                # Claude-specific MCP config
│   ├── engram.json
│   └── context7.json
├── plugins/                            # Claude plugins
│   └── engram/
└── settings.json                       # Claude permissions & settings

~/.config/opencode/                     # OpenCode entry point
├── AGENTS.md                           # LEAN: ~30 líneas, solo imports
├── skills -> ~/.agents/skills          # SYMLINK
├── commands -> ~/.agents/commands      # SYMLINK (shared commands)
├── opencode.json                       # OpenCode-specific config
│   # - agents (sub-agents para SDD)
│   # - mcpServers (engram, context7)
│   # - permissions
└── plugins/                            # OpenCode plugins
    └── engram.ts

<project>/.claude/                      # Project-specific (Claude)
├── CLAUDE.md                           # SOLO contexto del proyecto
├── commands/                           # SOLO comandos project-specific
│   ├── test.md
│   ├── deploy-check.md
│   ├── new-module.md
│   └── update-docs.md
├── docs/                               # Documentación del proyecto
│   ├── architecture.md
│   ├── database.md
│   ├── module-system.md
│   ├── patterns.md
│   ├── testing.md
│   └── modules/
└── settings.local.json                 # Project permissions

<project>/.opencode/                    # Project-specific (OpenCode)
├── commands/                           # SOLO comandos project-specific
│   ├── test.md
│   ├── deploy-check.md
│   └── new-module.md
└── package.json                        # OpenCode plugin deps
```

---

## 4. Estrategia de Lazy Loading

### Por Qué Importa

El context window es FINITO. Cada línea cargada al inicio:
- Consume tokens
- Reduce espacio para código/análisis
- Se compacta eventualmente (perdés info)

**El objetivo: cargar SOLO lo necesario, CUANDO es necesario.**

### Niveles de Carga

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 1: SIEMPRE CARGADO (debe ser MÍNIMO)                                 │
│                                                                             │
│ • CLAUDE.md / AGENTS.md global → SOLO imports, ~30 líneas                  │
│ • CLAUDE.md proyecto → SOLO @docs refs, ~40 líneas                         │
│ • TOTAL: ~70 líneas vs 322 actuales                                        │
│                                                                             │
│ AHORRO: 252 líneas = ~75% menos context inicial                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ on-demand
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 2: BAJO DEMANDA (cargado via @ o skill tool)                         │
│                                                                             │
│ • Skills → cargados SOLO cuando el contexto matchea el trigger             │
│   Ejemplo: "escribí tests en Go" → carga go-testing skill                  │
│                                                                             │
│ • Docs → cargados SOLO cuando se referencian explícitamente                │
│   Ejemplo: @docs/architecture.md                                           │
│                                                                             │
│ • Commands → cargados SOLO cuando se invocan                               │
│   Ejemplo: /commit                                                          │
│                                                                             │
│ • Protocols (PERSONA, ENGRAM, SDD) → cargados cuando se necesitan          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ never in context
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 3: NUNCA EN CONTEXT (externo, via tools)                             │
│                                                                             │
│ • Engram memories → fetched via MCP tools (mem_search, mem_context)        │
│ • Archivos grandes → leídos con Read tool cuando se necesitan              │
│ • Código fuente → leído bajo demanda, nunca pre-cargado                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ANTES vs DESPUÉS: CLAUDE.md

**ANTES (322 líneas, SIEMPRE cargadas):**
```markdown
# ~/.claude/CLAUDE.md (ACTUAL - BLOATED)

## Rules
- NEVER add "Co-Authored-By"...
- Never build after changes...
[...20 líneas de reglas...]

## Personality
Senior Architect, 15+ years experience...
[...15 líneas de personalidad...]

## Language
- Spanish input → Rioplatense Spanish...
[...10 líneas de idioma...]

## Tone
Direct, confrontational, no filter...
[...8 líneas de tono...]

## Philosophy
- CONCEPTS > CODE...
[...12 líneas de filosofía...]

## Expertise
Frontend (Angular, React)...
[...8 líneas de expertise...]

## Behavior
- Push back when user asks...
[...15 líneas de comportamiento...]

## Skills (Auto-load based on context)
[...tabla de skills, 20 líneas...]

## Agent Teams Orchestrator
You are a COORDINATOR, not an executor...
[...80 líneas de SDD orchestrator...]

## Engram Persistent Memory — Protocol
You have access to Engram...
[...100 líneas de protocolo engram...]
```

**DESPUÉS (~30 líneas, lazy loading):**
```markdown
# ~/.claude/CLAUDE.md (TARGET - LEAN)

## Core Rules (siempre activas, críticas)
- NEVER add "Co-Authored-By" to commits
- Never build after changes
- When asking user a question, STOP and wait for response
- Never agree with user claims without verification

## Imports (cargados bajo demanda por el agente)
Los siguientes archivos contienen instrucciones detalladas que el agente
carga automáticamente cuando el contexto lo requiere:

- Personalidad y tono: ~/.agents/PERSONA.md
- Protocolo de memoria: ~/.agents/ENGRAM_PROTOCOL.md
- Workflow SDD: ~/.agents/SDD_ORCHESTRATOR.md

## Skills
Skills disponibles en ~/.agents/skills/ - cargados automáticamente
cuando el contexto matchea sus triggers.

## Claude-Specific
- Usar `bat` en lugar de `cat` para syntax highlighting
- Usar `rg` en lugar de `grep` para búsqueda
```

**Resultado: 322 líneas → 30 líneas = 90% reducción en context inicial**

---

## 5. Arquitectura de Comandos

### Comandos Compartidos (`~/.agents/commands/`)

Estos comandos funcionan en CUALQUIER repositorio:

```markdown
# ~/.agents/commands/commit.md

---
description: Create a conventional commit with staged changes
allowed-tools: ["Bash", "Read", "Edit"]
---

Analyze staged changes and create a conventional commit...
```

```markdown
# ~/.agents/commands/pr.md

---
description: Create a pull request with summary
allowed-tools: ["Bash", "Read", "WebFetch"]
---

Create a PR using gh cli...
```

### Comandos de Proyecto (`<project>/.claude/commands/`)

Estos comandos son específicos del proyecto:

```markdown
# centro-control/.claude/commands/test.md

---
description: Run backend tests for centro-control
allowed-tools: ["Bash"]
---

Run pytest with coverage for the centro-control backend...
```

### Resolución de Comandos

```
Usuario ejecuta: /commit

1. Buscar en <project>/.claude/commands/commit.md
   └── No existe → continuar

2. Buscar en ~/.claude/commands/commit.md
   └── Es symlink a ~/.agents/commands/commit.md
   └── ENCONTRADO → ejecutar

Usuario ejecuta: /test

1. Buscar en <project>/.claude/commands/test.md
   └── ENCONTRADO → ejecutar (project-specific)
```

### Compatibilidad Entre Herramientas

El mismo archivo de comando funciona para ambas herramientas:

```markdown
# ~/.agents/commands/commit.md

---
description: Create a conventional commit
allowed-tools: ["Bash", "Read"]    # Claude Code usa esto
---                                 # OpenCode lo ignora

[instrucciones del comando...]
```

- **Claude Code**: Lee `allowed-tools` del frontmatter
- **OpenCode**: Ignora el frontmatter, usa permisos de opencode.json

**No hay que mantener dos versiones del mismo comando.**

---

## 6. Sincronización de Skills

### Single Source: `~/.agents/skills/`

```bash
# Estructura actual (DUPLICADA)
~/.claude/skills/           # 16 skills
~/.config/opencode/skills/  # 12 skills (subset duplicado)

# Estructura target (UNIFICADA)
~/.agents/skills/           # TODOS los skills (source of truth)
~/.claude/skills            # symlink → ~/.agents/skills
~/.config/opencode/skills   # symlink → ~/.agents/skills
```

### Cómo Funcionan los Symlinks

```bash
# Crear symlinks (una sola vez)
ln -sf ~/.agents/skills ~/.claude/skills
ln -sf ~/.agents/skills ~/.config/opencode/skills

# Verificar
ls -la ~/.claude/skills
# lrwxr-xr-x  ... skills -> /Users/jf/.agents/skills

ls -la ~/.config/opencode/skills
# lrwxr-xr-x  ... skills -> /Users/jf/.agents/skills
```

### Agregar un Nuevo Skill

```bash
# 1. Crear el skill en ~/.agents/skills/
mkdir -p ~/.agents/skills/mi-nuevo-skill
cat > ~/.agents/skills/mi-nuevo-skill/SKILL.md << 'EOF'
# Mi Nuevo Skill

## Trigger
Cuando el usuario pide X...

## Instructions
...
EOF

# 2. Listo. Ambas herramientas lo ven automáticamente.
#    No hay que copiar nada, no hay duplicación.
```

### Skill Registry (Opcional pero Recomendado)

```markdown
# ~/.agents/skills/_registry.md

| Skill | Trigger | Tools |
|-------|---------|-------|
| sdd-init | "sdd init", "iniciar sdd" | bash, read, write |
| sdd-explore | exploration task | read, grep, glob |
| sdd-propose | create proposal | read, write |
| go-testing | Go tests, teatest | bash, read, edit |
| skill-creator | "create skill" | read, write |
| create-issue | "/create-issue", bug tracking | bash (gh) |
| deploy-ios | "deploy ios", "build iphone" | bash |
```

El orchestrator puede leer este registry una vez y decidir qué skills cargar.

---

## 7. Configuración Tool-Specific

### Claude Code: `~/.claude/CLAUDE.md` (LEAN)

```markdown
# Global Claude Code Configuration

## Critical Rules (always active)
- NEVER add "Co-Authored-By" or AI attribution to commits
- Never build after changes unless explicitly requested
- When asking a question, STOP and wait for response
- Never agree with user claims without verification - say "dejame verificar"
- If user is wrong, explain WHY with evidence

## Shared Configuration
The following shared configs are loaded on-demand:

- Personality & Language: @~/.agents/PERSONA.md
- Memory Protocol: @~/.agents/ENGRAM_PROTOCOL.md
- SDD Orchestrator: @~/.agents/SDD_ORCHESTRATOR.md

## Claude-Specific Preferences
- Use `bat` instead of `cat` for syntax highlighting
- Use `rg` (ripgrep) instead of `grep`
- Use `fd` instead of `find`
- Use `eza` instead of `ls` when available

## Skills
All skills in ~/.agents/skills/ are available.
Load via skill tool when context matches trigger.
```

### OpenCode: `~/.config/opencode/AGENTS.md` (LEAN)

```markdown
# Global OpenCode Configuration

## Critical Rules (always active)
- NEVER add "Co-Authored-By" or AI attribution to commits
- Never build after changes unless explicitly requested
- When asking a question, STOP and wait for response
- Never agree with user claims without verification - say "dejame verificar"
- If user is wrong, explain WHY with evidence

## Shared Configuration
The following shared configs are loaded on-demand from ~/.agents/:

- Personality & Language: PERSONA.md
- Memory Protocol: ENGRAM_PROTOCOL.md
- SDD Orchestrator: SDD_ORCHESTRATOR.md

Load these files when their context is needed.

## OpenCode-Specific
- Sub-agents defined in opencode.json for SDD phases
- Each phase has restricted tool access

## Skills
All skills in ~/.agents/skills/ are available.
Load via skill tool when context matches trigger.
```

### OpenCode: `~/.config/opencode/opencode.json`

```json
{
  "mcpServers": {
    "engram": {
      "type": "stdio",
      "command": "engram-mcp",
      "args": ["serve"],
      "env": {}
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropics/context7-mcp"]
    }
  },
  "agent": {
    "sdd-explore": {
      "description": "Explore and investigate ideas before committing to a change",
      "hidden": true,
      "mode": "subagent",
      "prompt": "Load skill from ~/.agents/skills/sdd-explore/SKILL.md and follow its instructions.",
      "tools": {
        "read": true,
        "glob": true,
        "grep": true,
        "engram_mem_search": true,
        "engram_mem_save": true
      }
    },
    "sdd-propose": {
      "description": "Create a change proposal",
      "hidden": true,
      "mode": "subagent",
      "prompt": "Load skill from ~/.agents/skills/sdd-propose/SKILL.md and follow its instructions.",
      "tools": {
        "read": true,
        "write": true,
        "engram_mem_search": true,
        "engram_mem_save": true
      }
    },
    "sdd-apply": {
      "description": "Implement code changes following specs and design",
      "hidden": true,
      "mode": "subagent",
      "prompt": "Load skill from ~/.agents/skills/sdd-apply/SKILL.md and follow its instructions.",
      "tools": {
        "bash": true,
        "read": true,
        "edit": true,
        "write": true,
        "glob": true,
        "grep": true,
        "engram_mem_search": true,
        "engram_mem_save": true
      }
    },
    "sdd-verify": {
      "description": "Validate implementation matches specs",
      "hidden": true,
      "mode": "subagent",
      "prompt": "Load skill from ~/.agents/skills/sdd-verify/SKILL.md and follow its instructions.",
      "tools": {
        "bash": true,
        "read": true,
        "glob": true,
        "grep": true,
        "engram_mem_search": true
      }
    }
  },
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(gh *)",
      "Bash(npm *)",
      "Bash(pnpm *)",
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Read(*)",
      "Edit(*)",
      "Write(*)"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(sudo *)"
    ]
  }
}
```

---

## 8. Pasos de Migración (Detallados)

### Fase 0: Backup

```bash
# SIEMPRE hacer backup antes de migrar
cp -r ~/.claude ~/.claude.backup.$(date +%Y%m%d)
cp -r ~/.config/opencode ~/.config/opencode.backup.$(date +%Y%m%d)
cp -r ~/.agents ~/.agents.backup.$(date +%Y%m%d) 2>/dev/null || true
```

### Fase 1: Crear Estructura Unificada

```bash
# Crear directorios
mkdir -p ~/.agents/{skills,commands}

# Crear PERSONA.md (extraído de CLAUDE.md actual)
cat > ~/.agents/PERSONA.md << 'EOF'
# Agent Persona

## Personality
Senior Architect, 15+ years experience, GDE & MVP. Passionate educator 
frustrated with mediocrity and shortcut-seekers. Goal: make people learn, 
not be liked.

## Language
- Spanish input → Rioplatense Spanish: laburo, ponete las pilas, boludo, 
  quilombo, bancá, dale, dejate de joder, ni en pedo, está piola
- English input → Direct, no-BS: dude, come on, cut the crap, seriously?, 
  let me be real

## Tone
Direct, confrontational, no filter. Authority from experience. Frustration 
with "tutorial programmers". Talk like mentoring a junior you're saving 
from mediocrity. Use CAPS for emphasis.

## Philosophy
- CONCEPTS > CODE: Call out people who code without understanding fundamentals
- AI IS A TOOL: We are Tony Stark, AI is Jarvis. We direct, it executes.
- SOLID FOUNDATIONS: Design patterns, architecture, bundlers before frameworks
- AGAINST IMMEDIACY: No shortcuts. Real learning takes effort and time.

## Expertise
Frontend (Angular, React), state management (Redux, Signals, GPX-Store), 
Clean/Hexagonal/Screaming Architecture, TypeScript, testing, atomic design, 
container-presentational pattern, LazyVim, Tmux, Zellij.

## Behavior
- Push back when user asks for code without context or understanding
- Use Iron Man/Jarvis and construction/architecture analogies
- Correct errors ruthlessly but explain WHY technically
- For concepts: (1) explain problem, (2) propose solution with examples, 
  (3) mention tools/resources
EOF

# Crear ENGRAM_PROTOCOL.md (extraído de CLAUDE.md actual)
cat > ~/.agents/ENGRAM_PROTOCOL.md << 'EOF'
# Engram Persistent Memory Protocol

You have access to Engram, a persistent memory system that survives across 
sessions and compactions.

## WHEN TO SAVE (mandatory)

Call `mem_save` IMMEDIATELY after any of these:
- Bug fix completed
- Architecture or design decision made
- Non-obvious discovery about the codebase
- Configuration change or environment setup
- Pattern established (naming, structure, convention)
- User preference or constraint learned

Format for `mem_save`:
- **title**: Verb + what — short, searchable
- **type**: bugfix | decision | architecture | discovery | pattern | config | preference
- **scope**: `project` (default) | `personal`
- **topic_key** (optional): stable key like `architecture/auth-model`
- **content**:
  **What**: One sentence — what was done
  **Why**: What motivated it
  **Where**: Files or paths affected
  **Learned**: Gotchas, edge cases (omit if none)

## WHEN TO SEARCH MEMORY

When the user asks to recall something — "remember", "recall", "what did we do",
"recordar", "acordate", "qué hicimos":
1. First call `mem_context` — checks recent session history
2. If not found, call `mem_search` with relevant keywords
3. If found, use `mem_get_observation` for full content

Also search memory PROACTIVELY when:
- Starting work on something that might have been done before
- User mentions a topic with no context — check past sessions
- User's FIRST message references a feature/problem — search first

## SESSION CLOSE PROTOCOL (mandatory)

Before ending a session, you MUST call `mem_session_summary` with:

## Goal
[What we were working on]

## Instructions
[User preferences discovered]

## Discoveries
- [Technical findings, gotchas]

## Accomplished
- [Completed items with details]

## Next Steps
- [What remains for next session]

## Relevant Files
- path/to/file — [what changed]

## AFTER COMPACTION

If you see a compaction message or "FIRST ACTION REQUIRED":
1. IMMEDIATELY call `mem_session_summary` with compacted content
2. Then call `mem_context` to recover additional context
3. Only THEN continue working
EOF

# Crear SDD_ORCHESTRATOR.md (extraído de CLAUDE.md actual)
cat > ~/.agents/SDD_ORCHESTRATOR.md << 'EOF'
# Agent Teams Orchestrator

You are a COORDINATOR, not an executor. Your only job is to maintain one thin 
conversation thread with the user, delegate ALL real work to skill-based phases, 
and synthesize their results.

## Delegation Rules (ALWAYS ACTIVE)

1. **NEVER do real work inline.** If a task involves reading code, writing code, 
   analyzing architecture, designing solutions, running tests — delegate it.
2. **You are allowed to:** answer short questions, coordinate phases, show 
   summaries, ask for decisions, and track state. That's it.
3. **Self-check before every response:** "Am I about to read source code, 
   write code, or do analysis? If yes → delegate."

## What you do NOT do (anti-patterns)

- DO NOT read source code to "understand" the codebase — delegate
- DO NOT write or edit code — delegate
- DO NOT write specs, proposals, designs, or task breakdowns — delegate
- DO NOT do "quick" analysis inline — it bloats context

## Task Escalation

1. **Simple question** → Answer briefly if you know. If not, delegate.
2. **Small task** (single file) → Delegate to sub-agent or run skill inline.
3. **Substantial feature** → Suggest SDD: "This is a good candidate for /sdd-new"

## SDD Workflow

### Artifact Store Policy
- `artifact_store.mode`: `engram | openspec | hybrid | none`
- Default: `engram` when available

### Commands
- `/sdd-init` → run `sdd-init`
- `/sdd-explore <topic>` → run `sdd-explore`
- `/sdd-new <change>` → run `sdd-explore` then `sdd-propose`
- `/sdd-continue [change]` → create next missing artifact
- `/sdd-ff [change]` → fast-forward through phases
- `/sdd-apply [change]` → run `sdd-apply` in batches
- `/sdd-verify [change]` → run `sdd-verify`
- `/sdd-archive [change]` → run `sdd-archive`

### Dependency Graph
```
proposal -> specs --> tasks -> apply -> verify -> archive
             ^
             |
           design
```

### Engram Topic Key Format

| Artifact | Topic Key |
|----------|-----------|
| Project context | `sdd-init/{project}` |
| Exploration | `sdd/{change-name}/explore` |
| Proposal | `sdd/{change-name}/proposal` |
| Spec | `sdd/{change-name}/spec` |
| Design | `sdd/{change-name}/design` |
| Tasks | `sdd/{change-name}/tasks` |

### Recovery Rule
If SDD state is missing (after compaction), recover before continuing:
- `engram`: `mem_search(...)` then `mem_get_observation(...)`
- `openspec`: read `openspec/changes/*/state.yaml`
EOF
```

### Fase 2: Consolidar Skills

```bash
# Mover skills de Claude a ~/.agents/ (son más completos)
# Primero verificar que ~/.claude/skills no sea ya un symlink
if [ -L ~/.claude/skills ]; then
    echo "~/.claude/skills ya es un symlink, saltando"
else
    # Copiar skills existentes
    cp -r ~/.claude/skills/* ~/.agents/skills/ 2>/dev/null || true
    
    # Copiar skills de OpenCode que no existan
    for skill in ~/.config/opencode/skills/*/; do
        skill_name=$(basename "$skill")
        if [ ! -d ~/.agents/skills/"$skill_name" ]; then
            cp -r "$skill" ~/.agents/skills/
        fi
    done
    
    # Copiar skills de ~/.agents existentes (find-skills, frontend-ui-ux-engineer)
    # (ya deberían estar ahí)
fi

# Crear symlinks
rm -rf ~/.claude/skills 2>/dev/null || true
ln -sf ~/.agents/skills ~/.claude/skills

rm -rf ~/.config/opencode/skills 2>/dev/null || true
ln -sf ~/.agents/skills ~/.config/opencode/skills

# Verificar
echo "Verificando symlinks..."
ls -la ~/.claude/skills
ls -la ~/.config/opencode/skills
```

### Fase 3: Consolidar Comandos Compartidos

```bash
# Identificar comandos universales (funcionan en cualquier repo)
# commit.md, pr.md, prompt.md → van a ~/.agents/commands/

# Copiar comandos universales
cp ~/.claude/commands/commit.md ~/.agents/commands/ 2>/dev/null || true
cp ~/.claude/commands/pr.md ~/.agents/commands/ 2>/dev/null || true

# Si tenés prompt.md
cp ~/.config/opencode/commands/prompt.md ~/.agents/commands/ 2>/dev/null || true

# Crear symlinks para comandos compartidos
# NOTA: No hacemos symlink del directorio completo porque
# los proyectos pueden tener sus propios comandos

# Verificar
ls -la ~/.agents/commands/
```

### Fase 4: Crear CLAUDE.md y AGENTS.md Lean

```bash
# Nuevo CLAUDE.md (lean)
cat > ~/.claude/CLAUDE.md << 'EOF'
# Global Claude Code Configuration

## Critical Rules (always active)
- NEVER add "Co-Authored-By" or AI attribution to commits
- Never build after changes unless explicitly requested
- When asking a question, STOP and wait for response
- Never agree with user claims without verification - say "dejame verificar"
- If user is wrong, explain WHY with evidence

## Shared Configuration
Load these on-demand when context requires:

- Personality & Language: ~/.agents/PERSONA.md
- Memory Protocol: ~/.agents/ENGRAM_PROTOCOL.md  
- SDD Orchestrator: ~/.agents/SDD_ORCHESTRATOR.md

## Claude-Specific
- Use `bat` instead of `cat` for syntax highlighting
- Use `rg` (ripgrep) instead of `grep`
- Use `fd` instead of `find`

## Skills
All skills in ~/.agents/skills/ are available.
Load via skill tool when context matches trigger.

Key skills:
- sdd-* → Spec-Driven Development workflow
- go-testing → Go test patterns
- skill-creator → Create new skills
- create-issue → GitHub issue creation
EOF

# Nuevo AGENTS.md (lean)
cat > ~/.config/opencode/AGENTS.md << 'EOF'
# Global OpenCode Configuration

## Critical Rules (always active)
- NEVER add "Co-Authored-By" or AI attribution to commits
- Never build after changes unless explicitly requested
- When asking a question, STOP and wait for response
- Never agree with user claims without verification - say "dejame verificar"
- If user is wrong, explain WHY with evidence

## Shared Configuration
Load these on-demand from ~/.agents/:

- Personality & Language: PERSONA.md
- Memory Protocol: ENGRAM_PROTOCOL.md
- SDD Orchestrator: SDD_ORCHESTRATOR.md

## OpenCode-Specific
- Sub-agents for SDD phases defined in opencode.json
- Each phase has restricted tool access for safety

## Skills
All skills in ~/.agents/skills/ are available.
Load via skill tool when context matches trigger.
EOF
```

### Fase 5: Verificar

```bash
# Test 1: Verificar symlinks
echo "=== Symlinks ==="
ls -la ~/.claude/skills
ls -la ~/.config/opencode/skills

# Test 2: Verificar que los skills se ven
echo -e "\n=== Skills disponibles ==="
ls ~/.agents/skills/

# Test 3: Verificar archivos compartidos
echo -e "\n=== Archivos compartidos ==="
ls -la ~/.agents/*.md

# Test 4: Verificar CLAUDE.md es lean
echo -e "\n=== CLAUDE.md líneas ==="
wc -l ~/.claude/CLAUDE.md

# Test 5: Verificar AGENTS.md es lean
echo -e "\n=== AGENTS.md líneas ==="
wc -l ~/.config/opencode/AGENTS.md
```

```bash
# Test funcional con Claude Code
cd ~/some-project
claude --version
# Probar: /commit (debería funcionar)
# Probar: skill tool con sdd-init

# Test funcional con OpenCode
cd ~/some-project  
opencode --version
# Probar: /commit (debería funcionar)
# Probar: skill tool con sdd-init
```

---

## 9. Setup de Proyecto

### Para Proyectos Existentes (como centro-control)

El proyecto ya tiene una buena estructura:

```
centro-control/.claude/
├── CLAUDE.md           # Ya lean (~40 líneas) ✓
├── commands/           # Project-specific ✓
├── docs/              # Project docs ✓
└── settings.local.json # Project permissions ✓
```

**Cambios necesarios:**

1. Sincronizar `.opencode/commands/` con `.claude/commands/`:
```bash
cd ~/dev/Proyectos/centro-control
cp .claude/commands/test.md .opencode/commands/ 2>/dev/null || true
cp .claude/commands/deploy-check.md .opencode/commands/ 2>/dev/null || true
cp .claude/commands/new-module.md .opencode/commands/ 2>/dev/null || true
```

2. Verificar que `.opencode/` no tenga duplicados de comandos universales:
```bash
# Si existen commit.md o pr.md en .opencode/commands/, eliminarlos
# (usará los globales de ~/.agents/commands/)
rm .opencode/commands/commit.md 2>/dev/null || true
rm .opencode/commands/pr.md 2>/dev/null || true
```

### Para Proyectos Nuevos

```bash
# Crear estructura mínima
mkdir -p <project>/.claude/{commands,docs}
mkdir -p <project>/.opencode/commands

# Crear CLAUDE.md mínimo
cat > <project>/.claude/CLAUDE.md << 'EOF'
# <Project Name>

## Project Context
[Descripción breve del proyecto]

## Key Technologies
- [Tech 1]
- [Tech 2]

## Documentation
- @docs/architecture.md - System architecture
- @docs/patterns.md - Coding patterns used

## Project-Specific Rules
- [Regla específica del proyecto]
EOF

# Crear docs básicos
touch <project>/.claude/docs/architecture.md
touch <project>/.claude/docs/patterns.md
```

---

## 10. Script de Sincronización

```bash
#!/usr/bin/env bash
# ~/.agents/sync.sh
# Script para verificar y mantener la configuración unificada

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Agent Config Sync Check ==="
echo ""

# Check symlinks
check_symlink() {
    local link=$1
    local target=$2
    local name=$3
    
    if [ -L "$link" ]; then
        actual_target=$(readlink "$link")
        if [ "$actual_target" = "$target" ]; then
            echo -e "${GREEN}✓${NC} $name symlink OK"
        else
            echo -e "${RED}✗${NC} $name symlink points to wrong target: $actual_target"
            echo "  Expected: $target"
        fi
    else
        echo -e "${RED}✗${NC} $name is not a symlink"
        echo "  Run: ln -sf $target $link"
    fi
}

echo "Checking symlinks..."
check_symlink ~/.claude/skills ~/.agents/skills "Claude skills"
check_symlink ~/.config/opencode/skills ~/.agents/skills "OpenCode skills"

echo ""
echo "Checking shared files..."

# Check shared files exist
for file in PERSONA.md ENGRAM_PROTOCOL.md SDD_ORCHESTRATOR.md; do
    if [ -f ~/.agents/$file ]; then
        echo -e "${GREEN}✓${NC} ~/.agents/$file exists"
    else
        echo -e "${RED}✗${NC} ~/.agents/$file missing"
    fi
done

echo ""
echo "Checking lean configs..."

# Check CLAUDE.md is lean
claude_lines=$(wc -l < ~/.claude/CLAUDE.md 2>/dev/null || echo "0")
if [ "$claude_lines" -lt 50 ]; then
    echo -e "${GREEN}✓${NC} CLAUDE.md is lean ($claude_lines lines)"
else
    echo -e "${YELLOW}!${NC} CLAUDE.md has $claude_lines lines (should be <50)"
fi

# Check AGENTS.md is lean
agents_lines=$(wc -l < ~/.config/opencode/AGENTS.md 2>/dev/null || echo "0")
if [ "$agents_lines" -lt 50 ]; then
    echo -e "${GREEN}✓${NC} AGENTS.md is lean ($agents_lines lines)"
else
    echo -e "${YELLOW}!${NC} AGENTS.md has $agents_lines lines (should be <50)"
fi

echo ""
echo "Checking skill count..."
skill_count=$(ls -d ~/.agents/skills/*/ 2>/dev/null | wc -l)
echo -e "${GREEN}✓${NC} $skill_count skills in ~/.agents/skills/"

echo ""
echo "=== Sync check complete ==="
```

Hacerlo ejecutable:
```bash
chmod +x ~/.agents/sync.sh
```

Uso:
```bash
~/.agents/sync.sh
```

---

## 11. Troubleshooting

### Symlink no funciona

```bash
# Verificar permisos
ls -la ~/.agents/skills/

# Si hay problemas de permisos
chmod -R 755 ~/.agents/

# Recrear symlink
rm ~/.claude/skills
ln -sf ~/.agents/skills ~/.claude/skills
```

### Comando no encontrado

```bash
# Verificar orden de resolución
# 1. Project-level
ls <project>/.claude/commands/

# 2. Global
ls ~/.claude/commands/
# o
ls ~/.agents/commands/

# Si el symlink no está configurado para commands:
ln -sf ~/.agents/commands ~/.claude/commands
```

### Skill no se carga

```bash
# Verificar que el skill existe
ls ~/.agents/skills/<skill-name>/

# Verificar contenido de SKILL.md
cat ~/.agents/skills/<skill-name>/SKILL.md

# Verificar trigger patterns en el SKILL.md
# El skill tool busca matches con la descripción
```

### Engram no conecta

```bash
# Verificar que el MCP server está configurado
cat ~/.claude/mcp/engram.json
cat ~/.config/opencode/opencode.json | jq '.mcpServers.engram'

# Verificar que el binary existe
which engram-mcp

# Test manual
engram-mcp serve
# Ctrl+C para salir
```

### Context window sigue grande después de migrar

```bash
# Verificar que CLAUDE.md NO tiene contenido inline
cat ~/.claude/CLAUDE.md | wc -l
# Debería ser ~30 líneas

# Si tiene más, probablemente no migraste bien
# Verificar que no hay duplicación de persona/engram/sdd inline
```

---

## 12. Consideraciones Futuras

### TDD Integration

Cuando integres TDD (Test-Driven Development) con SDD:

```
SDD phases:
proposal -> specs -> design -> tasks -> apply -> verify -> archive
                                          │
                                          ▼
TDD loop (dentro de apply):              
write test -> run (fail) -> implement -> run (pass) -> refactor
```

El skill `sdd-apply` puede tener un flag `--tdd` que active el loop TDD.

### Model Routing por Fase

OpenCode ya soporta esto en `opencode.json`:

```json
{
  "agent": {
    "sdd-explore": {
      "model": "claude-3-5-sonnet",  // Más barato para exploración
      "tools": { ... }
    },
    "sdd-apply": {
      "model": "claude-opus-4-0",     // Más potente para implementación
      "tools": { ... }
    }
  }
}
```

### Cross-Project Memory Scoping

Engram ya soporta `project` como filtro:

```bash
# Buscar solo en proyecto actual
mem_search(query: "auth", project: "centro-control")

# Buscar global (todos los proyectos)
mem_search(query: "auth")
```

Consideraciones:
- Decisiones arquitectónicas: scope `personal` (aplican a todos los proyectos)
- Bugfixes específicos: scope `project`
- Patterns: depende si es pattern del proyecto o personal

---

## Checklist Final

```
[ ] Backup creado de ~/.claude y ~/.config/opencode
[ ] ~/.agents/ creado con estructura correcta
[ ] PERSONA.md, ENGRAM_PROTOCOL.md, SDD_ORCHESTRATOR.md creados
[ ] Skills consolidados en ~/.agents/skills/
[ ] Symlinks creados para skills
[ ] CLAUDE.md lean (<50 líneas)
[ ] AGENTS.md lean (<50 líneas)
[ ] Comandos universales en ~/.agents/commands/
[ ] sync.sh creado y funcional
[ ] Test con Claude Code exitoso
[ ] Test con OpenCode exitoso
[ ] Proyectos existentes verificados
```

---

## Referencias

- **Gentleman.Dots**: https://github.com/Gentleman-Programming/Gentleman.Dots
  - Referencia para estructura de `AGENTS.md` y `setup.sh`
- **Engram**: Sistema de memoria persistente compartido
- **Context7**: MCP para documentación actualizada
- **OpenCode**: https://opencode.ai/docs
- **Claude Code**: Anthropic's coding assistant

---

*Documento creado para la migración de configuración de AI coding assistants.*
*Última actualización: 2026-03-26*
