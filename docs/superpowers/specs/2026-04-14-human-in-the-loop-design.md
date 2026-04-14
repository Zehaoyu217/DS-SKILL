# Design: Human-in-the-Loop Upgrade for data-science-iteration skill

**Date:** 2026-04-14  
**Status:** Approved — pending implementation plan  
**Author:** brainstorming session (Jay + Claude)

---

## Problem

The data-science-iteration skill runs as a near-fully autonomous agent. The user can issue named commands (`status`, `ship`, `fork`, etc.) but the orchestrator decides everything in between. This causes two failure modes:

1. **Rigidity**: The agent over-anchors on prior lessons and iron laws when the user proposes something new. Example: user asks to try a different testing methodology; agent keeps citing "honest test" iron law instead of engaging with the proposed approach.

2. **Opacity**: The user has no natural moment to redirect the agent mid-phase. Actions happen without checkpoints.

---

## Goals

1. User can give guidance at any time and the agent anchors to it.
2. User can override any rule (contextually scoped, logged).
3. Agent does a relevance check before citing prior knowledge to push back — and pushes back at most once.
4. Agent narrates non-trivial decisions before acting, giving the user a redirect window.
5. User can trigger a collaborative brainstorm on-demand, at any phase.

---

## Non-goals

- Removing or weakening any iron law.
- Forcing a brainstorm at every iteration start (on-demand only).
- Permanent rule changes without explicit user intent.

---

## Architecture

The upgrade adds a **human layer** between the user and the agent's existing knowledge base:

```
User input
    ↓
[USER_GUIDANCE.md]          ← first-class workspace file; always read first
    ↓
[knowledge-lint]            ← do prior lessons / iron laws actually apply here?
    ↓
[decision narration]        ← checkpoint before each non-trivial action
    ↓
[agent acts]
    ↓
[override logged if needed] ← overrides/vN-override-NNN.md
```

**No existing iron laws, phase playbooks, or persona files are modified.**

---

## Files

### New files

| File | Purpose |
|---|---|
| `playbooks/human-in-the-loop.md` | Defines knowledge-lint, decision narration, and override protocols |
| `playbooks/collab-brainstorm.md` | Defines the `brainstorm` command flow |
| `templates/user-override.md` | Artifact template for logging user overrides |
| `templates/user-guidance.md` | Seed template for `USER_GUIDANCE.md` at workspace init |

### Modified files

| File | Change |
|---|---|
| `SKILL.md` | Add orchestration anchor instruction + 5 new user commands |
| `templates/state.schema.json` | Add 3 new fields: `user_guidance_file`, `active_overrides`, `verbosity` |
| `scripts/init_workspace.py` | Seed `USER_GUIDANCE.md` from template at workspace init; create `overrides/` directory |

---

## Component designs

### 1. `USER_GUIDANCE.md` — the attention anchor

Lives in `ds-workspace/`. Seeded empty at `/ds-init`. Updated whenever the user provides guidance, overrides, or redirects.

```markdown
# User Guidance — Live Intent Log

> This file is the orchestrator's PRIMARY anchor.
> Read it BEFORE consulting lessons.md, iron-laws, or prior findings.
> The most recent entry reflects the user's current intent.

## Current focus (auto-updated)
phase: <current>
last_updated: YYYY-MM-DDTHH:MM:SSZ
active_overrides: []
verbosity: normal   # quiet | normal | verbose

---

## Guidance entries (append-only, newest last)

### G-001 — YYYY-MM-DDTHH:MM:SSZ
**User said:** "<verbatim or close paraphrase>"
**Agent interpretation:** <what the agent understood; scope if override>
**Status:** active | superseded
**Supersedes:** (none) | G-NNN
```

The SKILL.md orchestration anchor instruction: **"Read `USER_GUIDANCE.md` at the start of every response before consulting any other knowledge artifact."**

---

### 2. `playbooks/human-in-the-loop.md` — three protocols

#### Protocol 1: Knowledge-lint

Before citing any lesson, iron law, or prior finding to *object* to a user proposal, run:

1. What is the user currently trying to do? (read `USER_GUIDANCE.md` § current focus)
2. What prior knowledge am I about to invoke?
3. Does it actually apply?
   - Same subject? (CV scheme ≠ feature selection)
   - Same context? (competition-mode law in daily mode → does not apply)
   - Still valid? Cross-reference `lessons.md` `superseded_by` chain — if the lesson has been superseded by a later entry, it does not apply
4. If any answer is NO → do not cite it. Engage with the proposal directly.
5. If all YES → raise it once with concrete reasoning. If user confirms, defer and log.

**Resolved example:** Agent wants to cite "honest test" iron law. Knowledge-lint: is the user violating holdout integrity, or proposing a *different methodology* for an honest test? If the latter — the law does not apply. Drop the pushback.

#### Protocol 2: Decision narration

Before every non-trivial action, output:

```
━━ Decision checkpoint ━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: <phase>  |  Version: v<N>  |  Mode: <mode>
About to:  <action>
Because:   <reason / gate requirement>
Relevant guidance: "<G-NNN text>" (active)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceeding — type anything to redirect.
```

Non-trivial = phase transitions, persona dispatches, writing plan/brainstorm files, choosing an approach, logging a run. Trivial = reading files, updating counters, writing journal entries.

When `verbosity: quiet`, omit the checkpoint block and act. When `verbosity: verbose`, expand "Because" with full chain-of-thought.

#### Protocol 3: Override handling

When user guidance conflicts with a rule or prior finding:

1. Infer scope:
   - "just try" / "for now" / "this once" → `this-iteration`
   - "from now on" / "always" → `session` (= until user says `guidance clear` or a new `/ds` invocation starts)
   - "update the rule" / "change the law" → `permanent` (confirm first)
   - Ambiguous → default `this-iteration`, state interpretation, ask if wrong
2. Append G-NNN to `USER_GUIDANCE.md`
3. If scope = `permanent`: write `overrides/vN-override-NNN.md` (template below), flag for review at SHIP
4. Do not raise this topic again this session

---

### 3. `playbooks/collab-brainstorm.md` — `brainstorm [topic]` command

Triggered by user typing `brainstorm` or `brainstorm <topic>`. Style: listen first (B), then structure (A).

**Step 0 — Surface context (silent)**  
Read: current phase, active hypotheses from `plans/vN.md`, last 3 journal entries, relevant `lessons.md` entries, active `USER_GUIDANCE.md` entries.

**Step 1 — Open the floor**

```
━━ Brainstorm session ━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: <phase>  |  v<N>  |  <mode> mode
Active hypotheses: <list>
Recent lessons: <list, 2-3 most relevant>
Active guidance: <G-NNN text>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What are you thinking?
```

**Step 2 — Up to 2 clarifying questions (one at a time)**  
Ask only if the user's response leaves the core concern or success criterion unclear. Skip if clear enough.

**Step 3 — Structured proposal**

Present 2-3 candidate approaches:

```markdown
## Approach A — <name>
- What it is
- Why it might work
- Why it might fail
- **Plan B if this fails:** Fall back to <B> because <reason>. Kill criterion: <what means "failed"?>

## Approach B — <name>
(same structure)

## Approach C — <name>
(same structure)

## My recommendation: A
<2 sentences comparing trade-offs>
```

**Step 4 — User picks or redirects**  
- Pick → write `runs/vN/brainstorm-vN-USER-<topic>.md` (using brainstorm template, tagged `triggered_by: user-collab`). Surfaces at next relevant gate as an alternative to auto-generated brainstorm.
- Redirect → loop back to Step 2/3.

**Step 5 — Optional: anchor**  
If the session produced a directional decision, append G-NNN to `USER_GUIDANCE.md`.

---

### 4. `templates/user-override.md`

```markdown
---
id: override-vN-NNN
version: {N}
timestamp: YYYY-MM-DDTHH:MM:SSZ
rule_overridden: <iron law # or lesson id or finding id>
rule_text_excerpt: <quoted fragment>
user_request: <verbatim or paraphrased>
agent_interpretation: <what the agent understood>
scope: this-iteration | session | permanent
conflict_summary: <one sentence: rule said X, user wants Y>
agent_pushback: <yes/no — if yes, what was said>
user_confirmation: yes | no
applied: true | false
---

# Override — v{N}-{NNN}

## Rule overridden
<quoted>

## User's request
<what the user asked>

## Why this override was accepted
<scope, user confirmation, relevance reasoning>

## Effect on this iteration
<what changes>

## Flag at SHIP
[ ] Reviewer: was this override appropriate given final results?
```

---

### 5. SKILL.md changes

**Orchestration anchor** (add near top, before loop description):

```markdown
## Orchestration anchor (read this first, every response)

Before consulting any knowledge artifact (lessons.md, iron-laws.md, prior findings),
read `ds-workspace/USER_GUIDANCE.md`. The most recent guidance entry is the primary
anchor for all decisions this response.

Then follow `playbooks/human-in-the-loop.md` for:
- Knowledge-lint (before citing prior knowledge to push back)
- Decision narration (before each non-trivial action)
- Override handling (when user guidance conflicts with a rule)
```

**New commands** (add to existing command table):

| Command | Effect |
|---|---|
| `brainstorm [topic]` | Open collaborative brainstorm — `playbooks/collab-brainstorm.md` |
| `override <rule> [scope]` | Explicitly override a rule; scope inferred if omitted |
| `verbosity <quiet\|normal\|verbose>` | Set narration level; updates `USER_GUIDANCE.md` header |
| `guidance` | Print current `USER_GUIDANCE.md` active entries |
| `why` | Agent explains its last decision with full chain-of-thought |

---

### 6. `templates/state.schema.json` additions

```json
"user_guidance_file": {
  "type": "string",
  "default": "USER_GUIDANCE.md",
  "description": "Path to the user guidance anchor file, relative to ds-workspace/"
},
"active_overrides": {
  "type": "array",
  "items": { "type": "string" },
  "description": "List of active override ids (override-vN-NNN) for this session",
  "default": []
},
"verbosity": {
  "type": "string",
  "enum": ["quiet", "normal", "verbose"],
  "default": "normal",
  "description": "Decision narration verbosity level"
}
```

---

## Interaction model summary

```
Normal execution:
  User message → read USER_GUIDANCE.md → knowledge-lint if needed →
  decision checkpoint → act → update USER_GUIDANCE.md if guidance received

On-demand brainstorm:
  "brainstorm [topic]" → surface context card → open question →
  ≤2 clarifying Qs → 2-3 structured approaches with Plan B →
  user picks → write brainstorm artifact → optionally anchor in USER_GUIDANCE.md

Override:
  User guidance conflicts with rule → infer scope → log G-NNN →
  if permanent: write override artifact → do not re-raise this session
```

---

## What this does NOT change

- Iron laws #1–19 are unchanged in text and enforcement.
- Phase gate files are still required; gates are still mechanical.
- Persona dispatch is still via independent subagents.
- Competition mode / daily mode behavior is unchanged.
- Consistency lint still runs at FINDINGS/MERGE/SHIP.

The human layer changes *when and how* the agent communicates and responds to the user. It does not weaken the rigor of the underlying loop.

---

## Open questions accepted (deferred)

- Should `USER_GUIDANCE.md` entries be surfaced on the dashboard? (Deferred — dashboard changes are a separate scope.)
- Should the `ds-state-surface.sh` hook also surface the latest G-NNN entry? (Likely yes — small addition to the hook, handle in implementation.)
- Should `brainstorm` output also be shown in the dashboard's step-journal panel? (Deferred.)
