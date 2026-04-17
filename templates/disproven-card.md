---
# Machine-readable claim block (consumed by scripts/consistency_lint.py).
id: v{N}-d{NNN}
kind: disproven
version: {N}
phase: FINDINGS | MERGE
hypothesis_id: H-v{N}-XX              # must exist in plans/v{N}.md
claim_tested: <verbatim from the original hypothesis>
direction_expected: positive | negative | neutral | mixed
direction_observed: positive | negative | neutral | mixed | inconclusive
subject: <feature|model|pipeline|data-subset>
metric:
  name: <primary metric name>
  mean: <float>
  cv_std: <float>
  ci95_low: <float>
  ci95_high: <float>
  lift_vs_baseline: <float>
evidence:
  runs: [runs/v{N}/metrics.json]
  plots: []
root_cause: data-assumption | stat-assumption | implementation-bug | confounder | selection-bias | shift | other
dgp_refs:
  - memo: dgp-memo.md
    section: "§7"
    prediction_id: P-{NNN}
    relation: contradicts | refines | unrelated
supersedes: []
superseded_by: null
lesson: <1–3 sentences — the generalizable takeaway>
promotion_vote:
  skeptic: y | n | pending
  statistician: y | n | pending
  # if both y → promote to ~/.claude/skills/ds-learnings/
status: open | closed | promoted
created_at: YYYY-MM-DDTHH:MM:SSZ
---

# Disproven v{N}-d{NNN}

## Hypothesis (verbatim)
H-v{N}-XX: <verbatim from plan>

## Why we believed it
<prior + intuition + any literature or DGP prediction that motivated this>

## Test protocol used
<how it was tested; link to notebook/run>

## Evidence against
<metric, plots, statistical test>

## Root cause of the miss
`{root_cause}` — <short explanation>

## Lesson (1–3 sentences)
<generalizable takeaway; this is what promotes to lessons.md and optionally to ds-learnings/>

## Promotion vote
- Skeptic: [y|n|pending]
- Statistician: [y|n|pending]

If both `y`, promote to `~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<lesson-slug>.md` and set `status: promoted`.
