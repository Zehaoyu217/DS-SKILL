---
kind: surrender
id: vN-surrender
vN: <integer>
emitted_at: <ISO-8601>
reason: exhaustion              # exhaustion | budget-capped | intrinsic-ceiling | assumption-falsified
emitted_by: auto                # auto (Iron Law #22) | orchestrator-proposed | user-forced
coverage_snapshot_ref: coverage.json
final_primary_metric: <number>
target_primary_metric: <number>
ship_target_met: false
secondary_metrics_summary:
  - { name: <str>, final_value: <num>, baseline_value: <num>, degraded: <bool> }
---

# Surrender card vN

## Declaration

This version terminates the autonomous iteration loop. No further runs will be issued
without explicit `reset-surrender` command from the user.

## Ceiling evidence

Summarize the evidence that every productive direction has been tried and exhausted:

- Pattern areas explored: <list from coverage.json>
- Pattern areas exhausted with ceiling_reason: <list>
- Pattern areas unexplored and WHY they were skipped: <list with reasons>
- Consecutive plateau versions: <N> (threshold: <autonomous.yaml.autonomy.exhaustion_threshold>)
- Best CV mean achieved: <num> (target: <num>)
- Adversarial-validation AUC trajectory: <list across versions>
- Top-5 features across versions (any stability?): <list>

## What was learned

Short bullets on what this run proved and disproved. Link the relevant
`findings/vN-fNNN.md` and `disproven/vN-dNNN.md` cards.

- Proved:
  -
- Disproved:
  -

## Remaining unknowns

Areas the loop did not get to resolve. If the user re-opens, these are the hypotheses
to revisit. Frame each as a concrete falsifiable test.

-
-

## Recommendation

One of:
- **Accept and ship current best** (final_primary_metric > threshold): proceed with Iron Law #16 submission using the best run-id; note that secondary metrics may have degraded.
- **Declare project infeasible at current data/scope**: data collection or reframing required before another attempt makes sense.
- **Pivot to a different decision entirely**: the original framing question may be the wrong question; suggest new framing below.

## Meta-Auditor sign-off

Signed when emitted in autonomous mode; blocks if auditor does not agree the ceiling is real.

- Meta-Auditor verdict: PASS | BLOCK
- If BLOCK: which direction was prematurely marked exhausted?
