---
# Machine-readable brainstorm metadata (consumed by scripts/consistency_lint.py).
id: brainstorm-v{N}-{PHASE}          # e.g., brainstorm-v2-DATA_PREP, brainstorm-v2-FEATURE_MODEL, brainstorm-v2-FEATURE_ENG, brainstorm-v2-TUNING
version: {N}
phase: DATA_PREP | FEATURE_MODEL | FEATURE_ENG | TUNING | OTHER
sub_topic: <optional, e.g., "missing-value-handling for col X" or "hyperparameter search strategy">
parent_plan: plan-v{N}
triggered_by: phase-entry | explorer-dispatch | event-<name>
alternatives_count: {>=3}            # consistency_lint enforces this >= 3
chosen_alternative_id: A1            # which of the listed alternatives was picked
rejected_alternative_ids: [A2, A3]
contingency_alternative_id: A2       # fallback if chosen fails kill-criterion
literature_refs: []                  # ids / citations from literature/vN-memo.md
disproven_refs: []                   # disproven/v*-d*.md ids this brainstorm is aware of
explorer_ref: null                   # path to audits/vN-explorer-<phase>.md if Explorer was dispatched
sign_offs:
  author: pending | signed           # the persona producing this brainstorm (usually Engineer, sometimes Explorer)
  skeptic_microaudit: optional | signed   # advisory in most phases, required at FEATURE_MODEL entry
created_at: YYYY-MM-DDTHH:MM:SSZ
---

# Brainstorm v{N} — {PHASE}{:sub_topic if any}

## Problem statement
<One or two sentences: what decision are we making? What are we optimizing for in this phase / sub-step?>

## Inputs consulted
- **Plan:** `plans/v{N}.md` (trigger: <which hypothesis / pre-registered decision this brainstorm serves>)
- **Literature:** `literature/v{N}-memo.md` sections <list>
- **Prior disproven cards:** <list of ids reviewed to avoid re-exploring dead ends>
- **DGP memo:** `dgp-memo.md` §<relevant sections>
- **Explorer (if dispatched):** `audits/v{N}-explorer-<phase>.md`
- **Data / diagnostics artifacts:** <list, e.g., `audits/v{N}-data-prep.md §2`, `runs/v{N-1}/plots/...`>

## Candidate approaches (≥ 3 required)

### A1 — <short name>
- **Description:** <what it is, in one paragraph>
- **Why it could work:** <mechanism, prior evidence, literature refs>
- **Why it might fail:** <failure modes, known limitations>
- **Cost / feasibility:** compute, data, implementation complexity, reproducibility risk
- **Literature / prior-art refs:** <citations>
- **Expected effect size (if modeling/feature/tuning):** <quantitative guess + rationale>

### A2 — <short name>
(same structure)

### A3 — <short name>
(same structure)

### A4+ (optional, add as many as useful)
...

## Picked approach and rationale
**Chosen:** A{id} — <short name>

**Why this over the others:**
<2–4 sentences explicitly comparing to A-rejected. Must reference at least one concrete tradeoff, not a vibe.>

## Rejected approaches and reasons
- **A{id}:** <one-line rationale>
- **A{id}:** <one-line rationale>

## Contingency plan
If the chosen approach fails its kill-criterion (<state the criterion explicitly>), fall back to **A{contingency_id}** because <rationale>.

Escalation trigger: <what observation would cause us to brainstorm again rather than fall back?>

## Open questions / risks being accepted
<List the known-unknowns we are explicitly choosing not to resolve now, and why deferring is acceptable.>

## Skeptic micro-audit (required at FEATURE_MODEL entry, advisory elsewhere)
- **Reviewer:** Skeptic (subagent)
- **Verdict:** accept | accept-with-caveats | request-rework
- **Notes:** <specific concerns: narrow option set? weak rationale? contingency implausible?>
- **Signed:** pending | signed

---

## Usage rules

1. **Minimum alternatives: 3.** Brainstorms with fewer are rejected by `consistency_lint` — narrow option sets are the laziness failure mode this artifact exists to prevent.
2. **"A1 = first thing that came to mind" is an anti-pattern.** If one alternative is clearly dominant at write-time, either (a) reframe the decision so there is a real choice, (b) add intentionally weaker alternatives and document them as such, or (c) skip the brainstorm and note in the phase audit that this decision was deterministic.
3. **Literature refs are not optional when the phase has a literature memo.** At FEATURE_MODEL entry, every alternative should cite either `literature/vN-memo.md` or a documented gap where the memo is silent.
4. **Contingency is not a placeholder.** It should be a concrete alternative from the list, not "try something else."
5. **Brainstorms are per-phase AND per-sub-decision.** It is expected that FEATURE_MODEL produces multiple brainstorms in one version: one for model family, one for feature representation, one for tuning strategy. Sub-topic in the frontmatter keeps them distinguishable.
6. **Brainstorms are versioned with the plan, not globally.** A new brainstorm file is written each vN — brainstorms do not supersede older ones, they stand as artifacts of what was considered at that point.
