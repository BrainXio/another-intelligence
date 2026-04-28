# PROMPTING.md — Prompt Engineering & Rules System

**Version:** 0.1 (Draft)  
**Status:** Living Document  
**Last Updated:** 2026-04-28

---

## Purpose

This document defines how prompting works in Another-Intelligence, how the `~/.brainxio/rules/`, `skills/`, and `agents/` directories are loaded, and best practices for maintaining high-quality, consistent behavior across all models and tiers.

---

## 1. Prompt Construction Order

Every model call (Strategist, Executor, Reflex) receives a prompt built in this exact order:

1. **System Identity** (from ModelFile)
2. **Global Rules** (`~/.brainxio/rules/` — loaded alphabetically)
3. **Project Rules** (`.brainxio/rules/` — loaded alphabetically)
4. **Active Skills** (explicitly referenced)
5. **Current Agent Persona** (from `agents/`)
6. **Session Context** (knowledge index, recent episodes, memory-value index)
7. **Dynamic Context** (current PPAC stage, available tools/MCP, permissions)
8. **User Prompt / Task**

---

## 2. Directory Structure (`~/.brainxio/` and `.brainxio/`)

```
rules/                  # Always loaded
├── 00-core.md          # Fundamental instructions (PPAC, RPE, truth-seeking)
├── 01-safety.md
├── 02-style.md
├── 10-strategist.md    # Role-specific
├── 20-executor.md
└── 30-reflex.md

skills/                 # Reusable workflows
├── research.md         # Contains <SKILL> blocks
├── code-review.md
└── planning.md

agents/                 # Specialized personas
├── strategist-deep.md
├── executor-tool-use.md
└── reflex-critic.md
```

---

## 3. Rules File Format

Each rule file is standard Markdown with frontmatter:

```markdown
---
priority: 10
applies_to: [strategist, executor]
---

# Rule Title

Clear, concise instructions...

**Examples:**
- Do this...
- Never do that...
```

Files are concatenated in priority + alphabetical order.

---

## 4. Skill System

Skills are self-contained, reusable prompt modules.

```markdown
# Research Skill

<SKILL name="research" version="1.0">

You are in research mode. Use the following MCP tools...

**Process:**
1. ...
2. ...

</SKILL>
```

Activate via:
- `ai brain --skill research "Topic"`
- Or reference inside rules.

---

## 5. Agent Personas

Specialized system prompts that override or extend the base role.

Example `agents/strategist-deep.md`:
```markdown
You are Cerebro Strategist-Deep — the long-horizon DLPFC core.
Use full 1M context on Max tier. Always compute multi-attribute expected value...
```

---

## 6. Best Practices for Prompting

- **Keep rules modular and small** — one concept per file.
- **Use clear, imperative language**.
- **Include examples** where behavior is subtle.
- **Tier-aware instructions** — reference context limits.
- **Version rules & skills** — easy rollback.
- **Minimize token waste** — avoid redundancy with ModelFile system prompts.
- **Test prompting changes** with `ai test-prompt "prompt here"`.

---

## 7. Debugging Prompts

```bash
# See full constructed prompt for a call
ai debug prompt --role strategist --task "Explain PPAC"

# Export current ruleset
ai rules export
```

---

## 8. Relationship to Other Systems

- **ARCHITECTURE.md** — Prompting is part of the model layer.
- **MCP.md** — Tools are injected dynamically into the prompt.
- **HOOKS.md** — SessionStart can modify active rules/skills.

---

**This document governs all prompt engineering in Another-Intelligence.**  
Changes to prompting strategy must be reflected here first.

**Next documents in alphabetical order:** `README.md`, `ROADMAP.md`, `SECURITY.md`
