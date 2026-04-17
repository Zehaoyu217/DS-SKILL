---
# Machine-readable claim block (consumed by scripts/consistency_lint.py).
# Every field is required unless noted optional.
id: v{N}-f{NNN}                       # globally unique; matches filename
kind: finding
version: {N}                          # integer; plan version that produced it
phase: FINDINGS                       # FRAME | DGP | AUDIT | DATA_PREP | EDA | FEATURE_MODEL | VALIDATE | FINDINGS | MERGE | SHIP
hypothesis_id: H-v{N}-XX              # must exist in plans/v{N}.md
claim: <specific, falsifiable one-liner>
direction: positive | negative | neutral | mixed
  # positive: feature/effect raises target; negative: lowers; neutral: no effect; mixed: interacts
subject: <feature|model|pipeline|data-subset>
  # what the claim is about — a column name, model family, cohort, etc.
metric:
  name: <primary metric name, e.g., auc, rmse, logloss>
  mean: <float>
  cv_std: <float>
  ci95_low: <float>
  ci95_high: <float>
  lift_vs_baseline: <float>           # positive means better than baseline
  seed_std: <float>                   # multi-seed stability (Iron Law #4)
  n_seeds: <int>                      # ≥3 for ship candidates
evidence:
  runs: [runs/v{N}/metrics.json]
  plots: []
  notebooks: [nb/v{N}_<slug>.ipynb]   # optional
dgp_refs:                             # which DGP memo predictions does this support or contradict?
  - memo: dgp-memo.md
    section: "§7"
    prediction_id: P-{NNN}            # id assigned in DGP §7 structured block
    relation: supports | contradicts | refines | unrelated
supersedes: []                        # list of earlier finding/disproven ids made obsolete
superseded_by: null                   # set when a later version invalidates this
confounders_considered: []
generalizability: project-local | promotable
next_step_implication: <one line>
status: open | confirmed | retracted
  # open: pending review; confirmed: Skeptic signed; retracted: later evidence overturned
sign_offs:
  skeptic: pending | signed | rejected
  statistician: pending | signed | rejected
created_at: YYYY-MM-DDTHH:MM:SSZ
---

# Finding v{N}-f{NNN}

## Claim
<repeat `claim` in prose; 1–3 sentences with context>

## Evidence
<metric + CI, link to `runs/v{N}/metrics.json`, plots>

## Confounders considered
<what alternatives were ruled out>

## Relation to DGP memo
<does this confirm a §7 prediction, contradict one, or surface something new? reference prediction_id(s)>

## Generalizability
project-local | promotable — <why>

## Next-step implication
<one line — feature kept, pipeline branch chosen, ablation queued, etc.>
