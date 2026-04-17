---
# Machine-readable plan metadata (consumed by scripts/consistency_lint.py).
id: plan-v{N}
version: {N}
parent_version: {N-1} | null
trigger_refs: []                      # list of finding/disproven ids or event names that produced this plan
pre_registration:
  primary_metric: <e.g., auc>
  uncertainty_method: <cv-std + bootstrap-ci95 + multi-seed>
  n_seeds_required: 3
  ship_criteria:
    min_lift_vs_baseline: <float>
    max_seed_std_ratio: 0.5           # seed_std < 0.5 * lift_vs_baseline
    max_predicted_gap: <float>        # 2·cv_std + λ·adv_auc_excess + μ·dup_ratio
  stop_rules: []                      # conditions under which iteration ends
hypotheses:
  - id: H-v{N}-01
    statement: <specific, falsifiable>
    rationale: <one line>
    expected_direction: positive | negative | neutral | mixed
    test_protocol: <what CV split, what comparison, what metric>
    kill_criterion: <what result would disprove>
    dgp_refs: []                      # prediction ids from DGP §7a this hypothesis tests
    status: open | resolved-finding | resolved-disproven
  - id: H-v{N}-02
    ...
sign_offs:
  skeptic: pending | signed
  validation_auditor: pending | signed
  literature_scout_lite: pending | signed
created_at: YYYY-MM-DDTHH:MM:SSZ
---

# Plan v{N}  (parent: v{N-1} | root)

## Trigger
<what from v{N-1} caused this plan — cite finding/disproven/event ids from `trigger_refs`>

## Goal for v{N}

## Primary metric (+ uncertainty method)
<matches `pre_registration.primary_metric` and `uncertainty_method` above>

## Hypotheses to test
Each hypothesis below must mirror an entry in the YAML `hypotheses:` block. At FINDINGS exit every `H-v{N}-XX` must resolve to exactly one `findings/vN-fNNN.md` or `disproven/vN-dNNN.md` (Iron Law #6).

- H-v{N}-01 — <statement>
- H-v{N}-02 — ...

## Scope in / out

## Pre-registered decisions (prevent post-hoc drift)
Ship criteria, CV scheme references, metric thresholds. These values must match the YAML `pre_registration:` block — `consistency_lint` flags divergence.

## Risks / blockers carried from v{N-1}

## Skeptic sign-off:  [pending|signed]
## Validation Auditor sign-off:  [pending|signed]
## Literature Scout (Lite memo) sign-off:  [pending|signed]
