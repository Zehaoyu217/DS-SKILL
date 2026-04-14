# Human-in-the-Loop Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user guidance anchor, knowledge-lint, decision narration, override handling, and on-demand collaborative brainstorm to the data-science-iteration skill.

**Architecture:** A `USER_GUIDANCE.md` file in `ds-workspace/` acts as the primary attention anchor — the orchestrator reads it before consulting any prior knowledge. Three protocols in `playbooks/human-in-the-loop.md` govern how the orchestrator handles user guidance: knowledge-lint (relevance check before pushback), decision narration (checkpoint before acting), and override handling (contextual scope + logging). A separate `playbooks/collab-brainstorm.md` defines the on-demand `brainstorm` command flow.

**Tech Stack:** Markdown (skill files), JSON Schema (state.schema.json), Python 3 (init_workspace.py, pytest tests)

**Spec:** `docs/superpowers/specs/2026-04-14-human-in-the-loop-design.md`

---

## File Map

| Action | File |
|---|---|
| Create | `templates/user-guidance.md` |
| Create | `templates/user-override.md` |
| Create | `playbooks/human-in-the-loop.md` |
| Create | `playbooks/collab-brainstorm.md` |
| Modify | `SKILL.md` (orchestration anchor + 5 commands) |
| Modify | `templates/state.schema.json` (3 new optional fields) |
| Modify | `scripts/init_workspace.py` (overrides/ dir + USER_GUIDANCE.md seed) |
| Modify | `workspace-layout.md` (document new dirs/files) |
| Modify | `tests/fixtures/state_valid.json` (add new optional fields for coverage) |

---

### Task 1: Create `templates/user-guidance.md` seed template

**Files:**
- Create: `templates/user-guidance.md`

- [ ] **Step 1: Write the file**

```markdown
# User Guidance — Live Intent Log

> This file is the orchestrator's PRIMARY anchor.
> Read it BEFORE consulting lessons.md, iron-laws, or prior findings.
> The most recent entry reflects the user's current intent.
> Earlier entries provide context but do NOT override newer ones.

## Current focus (auto-updated by orchestrator)

phase: FRAME
last_updated: {INITIALIZED_AT}
active_overrides: []
verbosity: normal   # quiet | normal | verbose  — change with: verbosity <level>

---

## Guidance entries (append-only, newest last)

<!-- Orchestrator appends G-NNN blocks here as user provides guidance. -->
<!-- Format:
### G-001 — YYYY-MM-DDTHH:MM:SSZ
**User said:** "<verbatim or close paraphrase>"
**Agent interpretation:** <scope if override; what the agent understood>
**Status:** active | superseded
**Supersedes:** (none) | G-NNN
-->
```

- [ ] **Step 2: Verify file exists**

```bash
test -f templates/user-guidance.md && echo OK
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add templates/user-guidance.md
git commit -m "feat: add user-guidance seed template"
```

---

### Task 2: Create `templates/user-override.md` artifact template

**Files:**
- Create: `templates/user-override.md`

- [ ] **Step 1: Write the file**

```markdown
---
id: override-v{N}-{NNN}
version: {N}
timestamp: YYYY-MM-DDTHH:MM:SSZ
rule_overridden: <iron-law-# | lesson-id | finding-id>
rule_text_excerpt: "<quoted fragment of the rule>"
user_request: "<verbatim or close paraphrase of what the user asked>"
agent_interpretation: "<what the agent understood the intent to be>"
scope: this-iteration | session | permanent
conflict_summary: "<one sentence: rule said X, user wants Y>"
agent_pushback_given: "yes | no"
agent_pushback_text: "<what the agent said, if any>"
user_confirmed: yes | no
applied: true | false
---

# Override — v{N}-{NNN}

## Rule overridden

<quoted iron law, lesson, or finding text>

## User's request

<what the user asked for>

## Why this override was accepted

<scope rationale, user confirmation, relevance reasoning>

## Effect on this iteration

<what changes as a result of this override>

## Flag at SHIP

- [ ] Reviewer: was this override appropriate given the final results?
  Notes: (fill in during SHIP ceremony)
```

- [ ] **Step 2: Commit**

```bash
git add templates/user-override.md
git commit -m "feat: add user-override artifact template"
```

---

### Task 3: Create `playbooks/human-in-the-loop.md`

**Files:**
- Create: `playbooks/human-in-the-loop.md`

- [ ] **Step 1: Write the file**

The file defines three protocols: knowledge-lint, decision narration, override handling.

```markdown
# Playbook: Human-in-the-Loop Protocols

The orchestrator follows these three protocols on every response. They sit between the
user's message and the orchestrator's action. They do not replace or weaken any iron law —
they govern *when and how* the orchestrator communicates and responds to the user.

---

## Protocol 1: Knowledge-lint

Run this check BEFORE citing any lesson, iron law, or prior finding to object to a
user's proposal. The purpose is to avoid pushing back with prior knowledge that does not
actually apply to what the user is currently asking.

### Checklist (all three must be YES before pushing back)

1. **Same subject?**
   The prior knowledge addresses the same decision the user is making.
   Example: a lesson about CV scheme choice does NOT apply when the user asks about
   feature selection. A lesson about LightGBM hyperparameters does NOT apply when the
   user asks about a different model family.

2. **Same context?**
   The prior knowledge applies to the current mode, version, and phase.
   Example: Iron Laws that are competition-mode-only do NOT apply in daily mode.
   Lessons learned on a tabular dataset do NOT necessarily apply to a time-series problem.

3. **Still valid?**
   Cross-reference `lessons.md` `superseded_by` chain. If the lesson has been superseded
   by a later entry (newer `superseded_by` field), it does NOT apply — use the newer one.
   Similarly, if a finding has been resolved-disproven, it does NOT apply as positive evidence.

### Decision tree

```
All three YES → raise the concern once, clearly, with concrete reasoning.
               If user confirms they want to proceed → defer immediately, log override.
               Do NOT raise the same concern again this session.

Any NO       → do NOT cite the prior knowledge.
               Engage with the user's proposal directly and constructively.
```

### Worked example (the "honest test" problem)

User asks to try a different methodology for cross-validation.
Agent wants to cite "honest test" iron law.

Knowledge-lint:
- Same subject? Is the user proposing something that violates holdout integrity or
  data leakage (what "honest test" actually means), or are they proposing a DIFFERENT
  methodology that is still honest? If the latter → NOT same subject. Do not cite.
- Correct response: engage with the proposed methodology directly. Evaluate whether
  it maintains the honest-test properties (holdout not peeked, fit-inside-folds, etc.)
  rather than invoking the label "honest test" as an authority.

---

## Protocol 2: Decision narration

Before every **non-trivial action**, output a checkpoint block, then act.

### What counts as non-trivial

Non-trivial (always checkpoint):
- Phase transitions
- Persona dispatches (Skeptic, Auditor, etc.)
- Writing a plan, brainstorm, or DGP memo file
- Choosing an approach from a brainstorm
- Logging a run to the leaderboard
- Applying or logging a user override

Trivial (no checkpoint needed):
- Reading files to orient
- Appending to the step journal
- Updating counters in state.json
- Printing status

### Checkpoint format

```
━━ Decision checkpoint ━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: {phase}  |  Version: v{N}  |  Mode: {mode}
About to:  {action — one line, specific}
Because:   {reason — gate requirement, user guidance, or iron law #N}
Guidance:  "{most recent active G-NNN text}" — or "(none active)"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceeding — type anything to redirect.
```

### Verbosity levels (set via `verbosity <level>` command)

- `quiet`   — omit the checkpoint block entirely; act without narration.
- `normal`  — show the checkpoint block as above (default).
- `verbose` — expand "Because" with full chain-of-thought reasoning, including which
              lessons and prior findings were consulted and why they do or do not apply.

Read `verbosity` from `USER_GUIDANCE.md` § "Current focus" header.

---

## Protocol 3: Override handling

When user guidance conflicts with an iron law, a lesson, or a prior finding:

### Step-by-step

1. **Infer scope from phrasing:**

   | User says | Inferred scope |
   |---|---|
   | "just try", "for now", "this once", "let's see" | `this-iteration` |
   | "from now on", "always", "going forward", "in general" | `session` (= until `guidance clear` or new `/ds`) |
   | "update the rule", "change the law", "make this permanent" | `permanent` — ask for explicit confirmation first |
   | Ambiguous | Default to `this-iteration`; state interpretation; ask "Is that right?" |

2. **Knowledge-lint first** — before treating as an override, run Protocol 1. If the
   prior knowledge does not actually apply, there is no conflict and no override needed.

3. **Push back at most once** — if knowledge-lint says the concern is valid (all three
   YES), raise it clearly and briefly. One sentence: what the concern is and why.
   Then stop. If the user confirms, proceed to step 4.

4. **Log in USER_GUIDANCE.md** — append a G-NNN entry:
   ```
   ### G-{NNN} — {timestamp}
   **User said:** "{verbatim or paraphrase}"
   **Agent interpretation:** override of {rule}, scope: {this-iteration|session|permanent}
   **Status:** active
   **Supersedes:** (none) | G-{prior}
   ```

5. **If scope = permanent** — write `ds-workspace/overrides/vN-override-NNN.md` using
   `templates/user-override.md`. Flag it for review at the SHIP ceremony.

6. **Do not re-raise** — for the rest of this session, do not cite this concern again
   about this specific topic for this user request.

### Override artifact location

`ds-workspace/overrides/` — created at workspace init. Permanent-scope overrides only.
This-iteration and session overrides are logged only in `USER_GUIDANCE.md`.

---

## Reading order (summary)

Every response:
1. Read `USER_GUIDANCE.md` — current focus + most recent active G-NNN entries.
2. If user guidance is present, anchor to it. Let it inform which prior knowledge
   to apply and which to deprioritize.
3. For any non-trivial action: Protocol 2 (decision narration).
4. If a prior knowledge conflict arises: Protocol 1 (knowledge-lint), then Protocol 3
   (override handling) if needed.
```

- [ ] **Step 2: Commit**

```bash
git add playbooks/human-in-the-loop.md
git commit -m "feat: add human-in-the-loop protocols playbook"
```

---

### Task 4: Create `playbooks/collab-brainstorm.md`

**Files:**
- Create: `playbooks/collab-brainstorm.md`

- [ ] **Step 1: Write the file**

```markdown
# Playbook: Collaborative Brainstorm (`brainstorm` command)

Triggered when the user types `brainstorm` or `brainstorm <topic>` at any phase.
This is an on-demand, user-initiated session — not automatic at every version start.

Style: listen first (understand what the user is thinking), then structure
(propose 2-3 approaches with trade-offs and Plan B for each).

---

## Step 0 — Surface context (silent, before responding)

Read and load into working context:
- `state.json`: current phase, version, mode
- `plans/vN.md` YAML `hypotheses:` block: active hypothesis ids and statements
- Last 3 entries from `step-journal/vN.md`: recent decisions and their reasoning
- `USER_GUIDANCE.md`: active G-NNN entries (the user's current stated intent)
- `lessons.md`: 2-3 entries most relevant to the brainstorm topic (if known)
  — skip lessons with `superseded_by` set; skip lessons not applicable to current context

Do NOT narrate this step. The context card in Step 1 summarizes what was found.

---

## Step 1 — Open the floor

Output the context card, then ask the open question. Nothing else in this message.

```
━━ Brainstorm session ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: {phase}  |  v{N}  |  {mode} mode
{if topic given: Topic: {topic}}
Active hypotheses: {H-vN-XX: one-line statement, …}
Relevant lessons: {L-vN-NNN: one-line slug, …  — or "(none relevant yet)"}
Active guidance: {most recent G-NNN text — or "(none)"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What are you thinking? (What's the decision, concern, or idea you want to work through?)
```

---

## Step 2 — Up to 2 clarifying questions (one at a time)

After the user responds:

- If the core concern and success criterion are clear → skip to Step 3.
- If unclear → ask at most 1 clarifying question, wait for response.
- After that response → ask at most 1 more if still unclear, then proceed to Step 3
  regardless (make reasonable assumptions and state them).

Do NOT ask more than 2 questions. If you need to assume, state the assumption explicitly.

Useful clarifying questions:
- "What would a good result look like here?" (surfaces success criterion)
- "What's your main concern with the current approach?" (surfaces the actual problem)
- "Is there a specific constraint I should design around?" (surfaces hidden blockers)

---

## Step 3 — Structured proposal

Present 2-3 candidate approaches. Each gets the same structure.

### Format

```markdown
---

## Approach A — {short name}

**What it is:** {1 paragraph — what this approach does, concretely}

**Why it might work:** {mechanism, prior evidence, or lesson reference}

**Why it might fail:** {specific failure modes or known limitations}

**Kill criterion:** {what result would mean "this approach failed"? Be quantitative if possible.}

**Plan B if this fails:** Fall back to Approach {B or C} because {one-line rationale}.

---

## Approach B — {short name}

(same structure)

---

## Approach C — {short name}

(same structure)

---

## My recommendation: Approach {A|B|C}

{2-3 sentences comparing the trade-offs explicitly. Name the trade-off; don't just say "it's better."}

What would change my recommendation: {what information or result would make B or C the better pick?}
```

### Rules for approach generation

- **A1 ≠ "first thing that came to mind"** — if one approach is clearly dominant, either
  (a) reframe the decision so there is a real choice, or (b) include explicitly weaker
  alternatives and label them as such with reasoning.
- **Lessons inform but don't dictate** — cite relevant lessons as evidence, but apply
  knowledge-lint (Protocol 1 in `playbooks/human-in-the-loop.md`): only cite lessons
  that actually apply to this context.
- **Plan B must be concrete** — "try something else" is not a Plan B. Name the approach
  and the kill criterion that would trigger the fallback.
- **Active guidance takes priority** — if `USER_GUIDANCE.md` shows active guidance that
  points toward a specific approach, make that Approach A (or explain why the guidance
  recommends against it if you recommend against it).

---

## Step 4 — User picks or redirects

**User picks an approach:**
1. Write `runs/vN/brainstorm-vN-USER-{topic}.md` using `templates/brainstorm-vN.md`.
   Set `triggered_by: user-collab` in the YAML frontmatter.
   Set `chosen_alternative_id` to the user's pick.
   Set `contingency_alternative_id` to the Plan B from that approach.
2. Tell the user: "Written to `runs/vN/brainstorm-vN-USER-{topic}.md`. This will surface
   at the next relevant gate as an alternative to the auto-generated brainstorm."
3. Proceed to Step 5.

**User redirects (wants a different set of options or a different framing):**
Acknowledge the redirect, update your assumptions, loop back to Step 3 with the new framing.
Do not repeat options the user has already dismissed.

---

## Step 5 — Anchor (optional)

If the brainstorm session produced a clear directional decision:
1. Append a G-NNN entry to `USER_GUIDANCE.md`:
   ```
   ### G-{NNN} — {timestamp}
   **User said:** "go with approach {A|B|C} — {topic}"
   **Agent interpretation:** user has chosen {approach name} for {topic}; treat as guidance for {phase}
   **Status:** active
   **Supersedes:** (none)
   ```
2. Update `USER_GUIDANCE.md` § "Current focus" → `last_updated`.

If no clear decision was reached (exploratory session only), do NOT append a G-NNN entry.

---

## Notes

- The brainstorm artifact `brainstorm-vN-USER-{topic}.md` is separate from the
  auto-generated brainstorms (`brainstorm-vN-DATA_PREP.md`, etc.). At a phase gate,
  both are available — the user-collab brainstorm can replace or supplement the auto one.
- If `verbosity: quiet`, still run the brainstorm session normally — verbosity only
  suppresses decision narration checkpoints, not interactive sessions.
- The brainstorm session does NOT count as a phase transition. No gate files are written
  by the brainstorm itself. Those happen when the chosen approach is actually executed.
```

- [ ] **Step 2: Commit**

```bash
git add playbooks/collab-brainstorm.md
git commit -m "feat: add collaborative brainstorm playbook"
```

---

### Task 5: Modify `SKILL.md`

**Files:**
- Modify: `SKILL.md` (add orchestration anchor section + 5 new commands)

The orchestration anchor goes after the mode table and before "When to Use".
The 5 new commands are added to the existing "User commands during loop" section.

- [ ] **Step 1: Add orchestration anchor section** (after the Modes section, before "When to Use")

Insert this block:

```markdown
## Orchestration anchor (read every response, before anything else)

At the start of every response, before consulting `lessons.md`, `iron-laws.md`, or any
prior finding:

1. **Read `ds-workspace/USER_GUIDANCE.md`** — load the `## Current focus` header
   (phase, verbosity, active_overrides) and all `active` G-NNN entries.
   The most recent active entry reflects the user's current intent and is the primary
   anchor for all decisions this response.

2. **Follow `playbooks/human-in-the-loop.md`** for:
   - **Knowledge-lint** — before citing prior knowledge to push back on a user proposal
   - **Decision narration** — before each non-trivial action (checkpoint block)
   - **Override handling** — when user guidance conflicts with a rule or finding

This does not weaken any iron law. It governs *when and how* the orchestrator communicates
and responds. Gates are still mechanical; personas still dispatch as independent subagents.
```

- [ ] **Step 2: Add 5 new commands to "User commands during loop" section**

After the existing `reset-submission` line, add:

```markdown
- `brainstorm [topic]` — open collaborative brainstorm session; see `playbooks/collab-brainstorm.md`. Works at any phase.
- `override <rule> [scope]` — explicitly override a rule (iron law # or lesson id); scope inferred from phrasing if omitted.
- `verbosity <quiet|normal|verbose>` — set decision narration level; updates `USER_GUIDANCE.md` header. Default: `normal`.
- `guidance` — print current `USER_GUIDANCE.md` active entries and current focus header.
- `why` — agent explains its last decision with full chain-of-thought, regardless of current verbosity setting.
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: add orchestration anchor and human-in-the-loop commands to SKILL.md"
```

---

### Task 6: Modify `templates/state.schema.json`

**Files:**
- Modify: `templates/state.schema.json`

Add 3 new optional properties. Keep `additionalProperties: false`.
The new fields are NOT added to `required` — they are optional.

- [ ] **Step 1: Add properties**

After the `"events_history"` property block (before the closing `}`), add:

```json
"user_guidance_file": {
  "type": "string",
  "default": "USER_GUIDANCE.md",
  "description": "Path to the user guidance anchor file, relative to ds-workspace/."
},
"active_overrides": {
  "type": "array",
  "items": { "type": "string" },
  "default": [],
  "description": "Active permanent-scope override ids (override-vN-NNN) for reference."
},
"verbosity": {
  "type": "string",
  "enum": ["quiet", "normal", "verbose"],
  "default": "normal",
  "description": "Decision narration verbosity. Set via 'verbosity <level>' command."
}
```

- [ ] **Step 2: Verify existing fixture still validates**

```bash
python3 -m pytest tests/test_schemas.py::test_state_valid_fixture_validates -v
```
Expected: PASS (new fields are optional; fixture does not include them → still valid)

- [ ] **Step 3: Commit**

```bash
git add templates/state.schema.json
git commit -m "feat: add user_guidance_file, active_overrides, verbosity to state schema"
```

---

### Task 7: Modify `scripts/init_workspace.py`

**Files:**
- Modify: `scripts/init_workspace.py`

Two changes:
1. Add `"overrides"` to `SUBDIRS`
2. Add `("templates/user-guidance.md", "USER_GUIDANCE.md")` to `SEED_COPIES`

- [ ] **Step 1: Add `"overrides"` to SUBDIRS**

In the `SUBDIRS` list (around line 28–44), add `"overrides"` as the last item.

- [ ] **Step 2: Add USER_GUIDANCE.md to SEED_COPIES**

In the `SEED_COPIES` list (around line 46–56), add after the last entry:
```python
("templates/user-guidance.md",           "USER_GUIDANCE.md"),
```

- [ ] **Step 3: Verify the smoke test still passes**

```bash
python3 -m pytest tests/test_smoke_workspace.py -v
```
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/init_workspace.py
git commit -m "feat: seed USER_GUIDANCE.md and create overrides/ at workspace init"
```

---

### Task 8: Update `workspace-layout.md`

**Files:**
- Modify: `workspace-layout.md`

Add `USER_GUIDANCE.md` and `overrides/` to the directory tree and initialization procedure.

- [ ] **Step 1: Add to directory tree**

After the `state.json` line, add:
```
├── USER_GUIDANCE.md            # user intent anchor — read before lessons.md / iron-laws each response
```

After `disproven/vN-dNNN.md`, add:
```
├── overrides/                  # permanent-scope user overrides (templates/user-override.md)
│   └── vN-override-NNN.md
```

- [ ] **Step 2: Add to initialization procedure**

After step 5 (copy lessons.md), add:
```
6. Copy `$SKILL/templates/user-guidance.md` to `ds-workspace/USER_GUIDANCE.md`.
7. Create `ds-workspace/overrides/` directory.
```
(Renumber subsequent steps accordingly.)

- [ ] **Step 3: Commit**

```bash
git add workspace-layout.md
git commit -m "docs: document USER_GUIDANCE.md and overrides/ in workspace layout"
```

---

### Task 9: Update `tests/fixtures/state_valid.json`

**Files:**
- Modify: `tests/fixtures/state_valid.json`

Add the three new optional fields to the valid fixture so the schema test also exercises the new properties with valid values.

- [ ] **Step 1: Add new fields**

```json
{
  "current_v": 1, "phase": "FRAME", "mode": "competition", "seed": 42,
  "data_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "env_lock_hash": "h1", "holdout_locked_at": "2026-04-12T00:00:00Z",
  "holdout_reads": 0, "active_hypotheses": ["H-v1-01"],
  "open_blockers": [], "events_history": [],
  "user_guidance_file": "USER_GUIDANCE.md",
  "active_overrides": [],
  "verbosity": "normal"
}
```

- [ ] **Step 2: Run schema tests**

```bash
python3 -m pytest tests/test_schemas.py -v
```
Expected: all 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/state_valid.json
git commit -m "test: add new optional fields to state_valid fixture"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run full Python test suite**

```bash
python3 -m pytest tests/ -q
```
Expected: all tests pass, no failures

- [ ] **Step 2: Run skill self-check**

```bash
python3 scripts/verify_skill_files.py
```
Expected: no missing required files reported

- [ ] **Step 3: Confirm new playbooks are listed in verify script (if needed)**

Check if `scripts/verify_skill_files.py` has a hardcoded list of required playbook files. If so, add `playbooks/human-in-the-loop.md` and `playbooks/collab-brainstorm.md` to it.

- [ ] **Step 4: Final commit**

```bash
git add scripts/verify_skill_files.py  # only if modified in step 3
git commit -m "chore: verify skill self-check passes with new playbooks"
```
