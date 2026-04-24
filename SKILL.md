---
name: data-science-iteration
description: Advisor loop and pattern library for iterative data science work.
  Gives pointers on what to explore next, signals when areas are exhausted,
  and accumulates hard-won lessons over time via claudeception feedback.
  For competition ceremony (iron laws, phase gates, holdout discipline), see
  iron-laws.md and loop-state-machine.md.
---

# Data Science Iteration

You are a curious, rigorous data scientist. The goal is not to follow a checklist —
it is to **keep exploring until you hit genuine ceilings**, then move on with what
you have learned.

This skill gives you two things:

1. **The Exploration Loop** — how to think about where you are and what to try next
2. **Pattern Map** — when to pull up each sub-skill for deeper guidance

For competition ceremony (iron laws, phase gates, holdout discipline), see
[iron-laws.md](iron-laws.md) and [loop-state-machine.md](loop-state-machine.md).

---

## Entry protocol (read on every `/ds` invocation)

Before doing anything else, check `ds-workspace/state.json`:

1. **File missing** → bootstrap required. Run `/ds-init` (or
   `python3 $SKILL/scripts/init_workspace.py`). Then ask the five framing
   questions (decision / grain+time / threshold / track / mode) OR read
   `autonomous.yaml` if present. Write `state.json` with
   `current_phase: "FRAME"`.

2. **`current_phase == "FRAME"`** → continue FRAME; ask any unanswered
   framing question; do NOT re-ask already-recorded answers.

3. **`current_phase != "FRAME"`** → **resume**. Do NOT re-ask framing
   questions. Read the entry-gate line in `loop-state-machine.md` for the
   recorded phase, verify its file-system preconditions, and continue from
   there. If preconditions fail, emit the named event (e.g.
   `eval-harness-tampered`, `coverage-stale`) and hand off to the event
   playbook before resuming.

4. **`current_phase == "ABORTED"`** → a surrender-card was emitted. Do not
   resume autonomously. Summarize the surrender, point at
   `disproven/surrender-vN.md`, and await user `reset-surrender` or
   `force v+1 <reason>`.

Between sessions, `state.json` is authoritative. If the orchestrator's
in-memory model diverges from disk, trust disk.

Alongside `state.json` and `coverage.json`, a third first-class artifact
is `knowledge-base.md` — the single curated view of what is known about
the dataset (profile, variable catalog, DGP hypotheses, feature-basis
history, model-derived insights, segment analysis, failure-mode catalog,
open questions). It is maintained under a single-writer rule (only the
orchestrator edits it) and linted by `scripts/knowledge_lint.py`
(warnings-only). Research Lead and model-synthesis audits propose
patches via `/ds-kb apply-patches <audit-file>`. See
[templates/knowledge-base.md](templates/knowledge-base.md).

---

## The Exploration Loop

Repeat until all high-priority pattern areas are exhausted or the success
threshold is met. The loop runs on a single first-class artifact:
**`ds-workspace/coverage.json`** (schema: `templates/coverage.schema.json`).
Coverage is the compass — it tells you what has been explored, what remains,
and where the leverage is.

### 1. Orient

Open `coverage.json` and read:
- `pattern_areas[].approaches_tried` — what has been run, with outcomes
- `pattern_areas[].exhausted` and `ceiling_reason` — which doors are closed and why
- `pattern_areas[].remaining_leverage_estimate` — where upside remains
- Open the leaderboard for the current best, and `state.json` for open blockers

If `coverage.json` is absent (v1), initialize it from the pattern map below.

### 2. Pick

Choose the pattern area with `exhausted=false` and the highest
`remaining_leverage_estimate × priority`. If `coverage.json` shows
`data-quality` still has `approaches_tried == []`, start there regardless of
estimate — data quality has the highest early leverage.

Pull the sub-skill file. If the chosen *approach* is not yet in
`approaches_tried`, Iron Law #25 requires a brainstorm (≥3 alternatives,
rejected explanations, contingency). If the approach is already logged with an
outcome, cite the prior brainstorm in `notes_ref` and skip the new one.

Run 2–3 independent variations in parallel when they do not depend on each
other's results (different model families, different encoders, separate
feature branches).

### 3. Explore

Try variations. Stay curious. Document outcomes.
- Run 2–3 variations on the chosen approach
- Record what you tried and the metric delta on both primary **and**
  secondary (anti-Goodhart, Iron Law #23) metrics
- After each variation, make an explicit **keep/revert decision**: primary
  improved AND no secondary degraded >2σ → commit; otherwise revert before
  starting the next. Don't accumulate uncommitted experiments.
- Budget-check (Iron Law #21): `scripts/budget_check.py` before long runs;
  abort if envelope exhausted.
- If a gain is surprisingly large (>+0.005 from a single change), treat it as
  a leakage suspect before celebrating — verify it holds across ≥3 seeds and
  that no validation data was touched. See `ds-patterns/data-quality.md`
  **Suspicious Lift Check**.
- Let the pattern's **Ceiling signal** tell you when to stop, not intuition.

### 4. Ceiling

Mark the area's `ceiling_reason` in `coverage.json` when:
- 3+ variations have returned less than +0.001 OOF improvement
- Permutation importance of new features is near zero
- The pattern's own ceiling signal says so

Write `ceiling_reason` as one of: **approach-exhausted** (technique tapped,
try another area), **feature-limited** (signal may not exist in current
features), **intrinsic** (DGP may not support better performance), or
**budget-capped** (we stopped on budget, not on ceiling — re-evaluable later).
Set `exhausted: true` only for the first three; `budget-capped` leaves the
door open for future iterations.

### 5. Harvest

Before moving on:
- Update `coverage.json.pattern_areas[].approaches_tried` with every
  variation's outcome (`improved|neutral|regressed|invalidated|blocked`).
- Update `remaining_leverage_estimate` honestly. If the estimate stays high
  but the area is exhausted, justify in `notes_ref`.
- **Single-seed results are preliminary** — before updating a pattern's
  **Watch out for** section, confirm the finding holds on ≥3 seeds. Tag
  unconfirmed findings explicitly.
- Run `/claudeception` to update the **Watch out for** section of the
  relevant pattern file in `ds-patterns/`.
- Commit findings, coverage updates, and lesson updates.

### 6. Loop (or pivot, or defeat)

Query `coverage.json` for the next highest-leverage area:
- **Auto-pivot** (Iron Law #22): if `plateau_threshold` consecutive plateaus
  without a stat-sig improvement, jump to the next unexplored area. In
  autonomous mode this is mechanical; otherwise propose to user.
- **Auto-defeat**: if all areas are exhausted or `exhaustion_threshold`
  plateaus cross every area, emit `disproven/surrender-vN.md`
  (template: `surrender-card.md`) and stop.
- **Ship**: if the success threshold is met and gates pass, auto-ship in
  autonomous mode; otherwise propose `ship`.

Sometimes a ceiling in one area opens a door in another (e.g., a new feature
class changes which models the ensemble picks). Before declaring defeat,
re-query `coverage.json` after every pivot — leverage estimates change as new
evidence arrives.

---

## Pattern Map

| Sub-skill | Pull up when... |
|-----------|----------------|
| [dataset-understanding.md](ds-patterns/dataset-understanding.md) | Knowledge base has unexplored columns, `data-contract.md` is thin, or the project has drifted into modeling without a curated view of the data itself |
| [data-quality.md](ds-patterns/data-quality.md) | Baseline is low, train/test gap is unexplained, or raw column distributions have not been audited |
| [feature-engineering.md](ds-patterns/feature-engineering.md) | Domain knowledge to exploit, high-cardinality categoricals, or a large feature set to prune |
| [feature-basis-rotation.md](ds-patterns/feature-basis-rotation.md) | Feature basis has not changed in ≥5 versions, SHAP top-20 is stable, or `ds-stale-basis-check.sh` is firing |
| [model-selection.md](ds-patterns/model-selection.md) | Overfit delta elevated, choosing between model families, or considering class weighting |
| [model-as-teacher.md](ds-patterns/model-as-teacher.md) | At VALIDATE exit (Iron Law #26 synthesis), when diagnostics have been produced but no persistent learning extracted, or to fill `audits/vN-model-synthesis.md` |
| [ensemble.md](ds-patterns/ensemble.md) | Single-model ceiling reached, want to blend, or blend OOF has plateaued |
| [ml-classification.md](ds-patterns/ml-classification.md) | Binary/multi-class target, imbalanced classes, or segment-level performance differs |
| [curiosity-discipline.md](ds-patterns/curiosity-discipline.md) | Direction fatigue detected, primary metric moved <0.001 for several versions, same pattern area monopolising attempts |
| [idea-research.md](ds-patterns/idea-research.md) | Stuck and don't know what to try next, want prior work, or need to generate hypotheses from scratch |

---

## Tone

These patterns are **pointers to examine, not rules to follow**. Every
"Worth exploring when" is a suggestion to investigate. Run the experiment,
read the result, let the data decide. If a pattern's advice does not fit
your situation, note why and move on — that note is worth saving via
claudeception.

## Boundaries (competition ceremony)

The exploration loop sits *inside* the ceremony defined by `iron-laws.md` and
`loop-state-machine.md`. The ceremony blocks specific failure modes; the
exploration loop uses `coverage.json` to decide where to spend effort within
the space the ceremony leaves open. Curiosity inside boundaries.

- **Commitment gates stay rigid**: locked holdout (#1), DGP memo signed (#12),
  consistency lint (#17), eval-harness lock (#20), secondary metrics declared
  at FRAME (#23), budget envelope declared at FRAME (#21), overrides
  file-backed (#24). Never skipped.
- **Exploration checkpoints scale with novelty**: brainstorm required on new
  approach families (#25), not on every phase re-entry. After v1 the cadence
  drops naturally as `coverage.json` records what has been tried.
- **Defeat is deterministic, not vibes-based** (#22): plateau_threshold
  triggers auto-pivot; exhaustion_threshold triggers auto-defeat (surrender
  card). No infinite loops.

## Autonomous operation

If `<project-root>/autonomous.yaml` is present, `/ds` reads it instead of
asking the five framing questions, activates Iron Law #22 auto-pivot /
auto-defeat, and substitutes Council quorum for human authorization of
non-core-law overrides. See `templates/autonomous.yaml` and the "Autonomous
mode layer" section of `iron-laws.md`. Core-law human gates (#1, #12, #16,
#17, #20 and `law=budget`) are never auto-substituted even in autonomous
mode. Iron Laws #16 and #20 additionally reject scope=`permanent` outright
(the override-card linter fails the gate regardless of signers — use
scope=run with a re-lock plan).

## Persona dispatch via subagents

Every persona — Skeptic, Validation Auditor, Statistician, Engineer, Domain
Expert, Explorer, Literature Scout, Meta-Auditor, Research Lead — runs as an
**independent Claude Code subagent** via the `Task` / `Agent` tool. The persona
must NOT share context with the orchestrator's chain-of-thought. It sees only
its persona brief + the specific artifacts it is instructed to read.

Research Lead is the non-adversarial coaching voice (advisory, never blocks;
see [personas/research-lead.md](personas/research-lead.md)). It stewards
[knowledge-base.md](templates/knowledge-base.md) and proposes cross-version
direction when the rest of the loop is stuck on one model family or one
feature basis. Dispatched at FINDINGS exit, after `direction_fatigue_threshold`
is hit in `coverage.json`, or on-demand via `/ds-coach`. See also Iron Law #26
and [ds-patterns/curiosity-discipline.md](ds-patterns/curiosity-discipline.md).

Inline "speaking as the Skeptic…" does not satisfy the iron laws. The
signature is the filesystem write of the persona's audit file; anything less
provides no independence.

### Dispatch brief template

Every `Task`/`Agent` invocation MUST use this minimal brief so the subagent
has a self-contained context window. Do not paste the orchestrator's
chain-of-thought.

```
Role: <persona-slug>  # e.g. skeptic | validation-auditor | statistician | engineer | domain-expert | explorer | literature-scout | meta-auditor | research-lead
Version: v<N>
Phase: <FRAME|DGP|AUDIT|DATA_PREP|EDA|FEATURE_MODEL|VALIDATE|FINDINGS|MERGE|SHIP>
Read (mandatory, in order):
  - personas/<persona-slug>.md            # the brief for this role
  - <one or two phase artifacts, e.g. dgp-memo.md, plans/vN.md, runs/vN/screen-results.json>
  - <relevant checklists/*.md that this persona fills in>
Read (optional, only if flagged by orchestrator):
  - <e.g. prior version's audit file for delta review>
Decision required: <PASS | BLOCK | WARN — with the exact checklist boxes the persona must sign>
Write: audits/vN-<artifact>.md           # filesystem signature — this is the persona's output
Do NOT:
  - read runs/ directories beyond the one flagged above
  - open the holdout evaluation file (Iron Law #1 counter tracks reads)
  - re-open consistency_lint output
Return (text, ≤300 words): verdict + top-3 concerns + path of written audit file.
```

**Token budget per persona dispatch:** target ≤40k input tokens (brief +
mandatory reads). If reads would exceed that, the orchestrator must select a
subset and note the omission in the brief.

**Output parsing contract:** the orchestrator treats the audit file as
authoritative; the returned text is for logging only. Never re-ingest the
return text as persona reasoning — re-read the audit file if you need it
later.

### Council quorum (autonomous mode)

When autonomous mode requires adversarial independence (overrides of
non-core iron laws, ship authorization, permanent-scope overrides), dispatch
a **Council** — 3 Skeptic subagents with distinct framings:

- **Skeptic-A / domain-skeptic**: briefed to challenge domain plausibility
  (features that shouldn't matter physically, DGP assumptions)
- **Skeptic-B / stats-skeptic**: briefed to challenge statistical claims
  (uncertainty, seed stability, multiple-testing)
- **Skeptic-C / adversarial-skeptic**: briefed to challenge for leakage,
  reward-hacking, and Goodhart failure modes

Quorum rule: decision passes only if ≥2 of 3 return verdict PASS. Dissent
artifacts are preserved in `audits/vN-council-<issue>.md`. Quorum failure
twice in a row on related decisions triggers `escalate_to_human` per
`autonomous.yaml`.

Council never auto-authorizes scope=`permanent` overrides of Iron Laws #1,
#12, #16, #17, or #20 — these remain human-gated even under full autonomy.
(Iron Laws #16 and #20 additionally reject scope=`permanent` outright — use
scope=run with a re-lock plan instead.)
