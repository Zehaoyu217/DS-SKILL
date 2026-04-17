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
   by a later entry (a newer entry with `superseded_by` pointing to this one), it does NOT
   apply — use the newer entry instead. Similarly, if a finding has `status: resolved-disproven`,
   it does NOT serve as positive evidence.

### Decision tree

```
All three YES → raise the concern once, clearly, with concrete reasoning.
               If user confirms they want to proceed → defer immediately, log override.
               Do NOT raise the same concern again this session.

Any NO       → do NOT cite the prior knowledge.
               Engage with the user's proposal directly and constructively.
```

### Worked example — the "honest test" problem

User asks to try a different methodology for cross-validation.
Agent wants to cite "honest test" iron law.

Knowledge-lint:
- Same subject? Is the user proposing something that violates holdout integrity or
  data leakage (what "honest test" actually means), or proposing a DIFFERENT methodology
  that is still honest? If the latter → NOT same subject. Do not cite.
- Correct response: engage with the proposed methodology directly. Evaluate whether
  it maintains the honest-test properties (holdout not peeked, fit-inside-folds, etc.)
  rather than invoking the label "honest test" as an authority.

---

## Protocol 2: Decision narration

Before every **non-trivial action**, output a checkpoint block, then act.

### What counts as non-trivial

Non-trivial (always checkpoint):
- Phase transitions
- Persona dispatches (Skeptic, Auditor, Statistician, etc.)
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
━━ Decision checkpoint ━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: {phase}  |  Version: v{N}  |  Mode: {mode}
About to:  {action — one line, specific}
Because:   {reason — gate requirement, user guidance, or iron law reference}
Guidance:  "{most recent active G-NNN text}" — or "(none active)"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceeding — type anything to redirect.
```

### Verbosity levels (set via `verbosity <level>` command)

- `quiet`   — omit the checkpoint block entirely; act without narration.
- `normal`  — show the checkpoint block as above (default).
- `verbose` — expand "Because" with full chain-of-thought: which lessons and prior
              findings were consulted, why they do or do not apply (knowledge-lint
              result), and what alternatives were considered.

Read `verbosity` from `USER_GUIDANCE.md` § "Current focus" header.

---

## Protocol 3: Override handling

When user guidance conflicts with an iron law, a lesson, or a prior finding:

### Step-by-step

1. **Infer scope from phrasing** (maps to Iron Law #24 override scope):

   | User phrasing | Conversational scope | Override-card scope |
   |---|---|---|
   | "just try", "for now", "this once", "let's see" | this-iteration | `run` |
   | "from now on", "always", "going forward", "in general" | session | `version` |
   | "update the rule", "change the law", "make this permanent" | permanent — ask for explicit confirmation before proceeding | `permanent` |
   | Ambiguous | Default to this-iteration; state interpretation; ask "Is that right?" | `run` |

2. **Knowledge-lint first** — before treating as an override, run Protocol 1. If the
   prior knowledge does not actually apply, there is no conflict and no override needed.
   Proceed with the user's request directly.

3. **Push back at most once** — if knowledge-lint says the concern is valid (all three
   YES), raise it clearly and briefly. One to two sentences: what the concern is and why.
   Then wait. If the user confirms they want to proceed anyway, proceed to step 4.

4. **Log in USER_GUIDANCE.md** — append a G-NNN entry:
   ```
   ### G-{NNN} — {timestamp}
   **User said:** "{verbatim or paraphrase}"
   **Agent interpretation:** override of {rule reference}, scope: {scope}
   **Status:** active
   **Supersedes:** (none) | G-{prior-id if superseding an earlier entry}
   ```
   Also update the `## Current focus` header: `last_updated` and `active_overrides`.

5. **Write the override-card artifact** (Iron Law #24) at
   `ds-workspace/overrides/vN-override-<law-slug>.md` using
   [templates/override-card.md](../templates/override-card.md). Required fields:
   - `scope` from step 1's table (`run` | `version` | `permanent`).
   - `signed_by: [user, ...]` (YAML list). Add `council` entries when Council quorum applies (autonomous mode, scope=`permanent`).
   - `user_guidance_ref: G-NNN` — ties artifact to step 4's entry.
   - `expires_at` — run end / vN rollover / `null` (permanent).
   - `agent_pushback_given` + `agent_pushback_text` — recorded from step 3.
   - **Core-law guard:** #1, #12, #16, #17, #20, `law=budget` require `user` in `signed_by` at any scope. Laws #16 and #20 reject `scope=permanent` outright (use `scope=run` + re-lock plan).

   Append the override id to `state.active_overrides`. Scope=`permanent` is flagged for SHIP re-authorisation; run/version expire automatically.

6. **Do not re-raise** — for the rest of this session, do not cite this specific
   concern again about this specific topic in the context of this user request.

---

## Reading order (every response)

1. Read `ds-workspace/USER_GUIDANCE.md` — load `## Current focus` header (verbosity,
   active_overrides) and all `active` G-NNN entries.
1a. **At FRAME entry and FEATURE_MODEL entry only:** Also read `ds-workspace/research-program.md`
   — load active hypotheses (H-rp-NNN), feature candidates, model candidates, and excluded
   approaches. Pass this as advisory context to Explorer subagent dispatch: Explorer *may*
   address user-nominated items but is not required to explore every one. If
   `research-program.md` does not exist (pre-feature workspace), create a stub from
   `templates/research-program.md` and note the creation in the step-journal.
2. Let active guidance anchor which prior knowledge to apply and which to deprioritize.
3. For any non-trivial action → Protocol 2 (decision narration checkpoint).
4. If a prior-knowledge conflict arises → Protocol 1 (knowledge-lint), then Protocol 3
   (override handling) if knowledge-lint says the concern is valid.
