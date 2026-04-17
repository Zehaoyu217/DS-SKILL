---
id: tuning-plan-v{N}
version: {N}
parent_brainstorm: brainstorm-v{N}-TUNING
model_family: "<e.g., lightgbm / xgboost / sklearn-random-forest / linear>"
strategy: "<grid | random | bayesian | halving | manual>"
budget_trials: {int}
budget_wall_time_minutes: {int}
nested_cv:
  outer_folds: {int}   # MUST match DGP cv-scheme outer
  inner_folds: {int}   # for tuning — MUST be nested inside outer folds (Iron Law #4)
seed: {int}
multi_seed: [{s1}, {s2}, {s3}]   # final tuned configuration is re-run across these
default_params_run_ref: runs/v{N}/<run_id>   # MANDATORY — tuning lift is measured against this
literature_refs:
  - memo: literature/v{N}-memo.md
    technique: "<e.g., LightGBM paper recommended num_leaves < 2^max_depth>"
sign_offs:
  author: ""         # Engineer
  skeptic_review: "" # Skeptic reviews for "tuning-as-p-hacking" risk
status: draft         # draft → approved → executed → superseded
---

# Tuning Plan v{N}

> **Before any tuned run is executed, this file must be `status: approved` and a `feature_baseline: true` feature-baseline run + a `default_params: true` run (using the model family's library defaults) must exist on the leaderboard.**
> **Tuning lift is always reported as `tuning_lift_vs_default`, never against the model baseline or feature baseline.** (Iron Law #19b)

## 1. What we're tuning and why

- Chosen model family: <name>; rationale link to `runs/v{N}/brainstorm-v{N}-FEATURE_MODEL.md` chosen alternative.
- Hypothesis: what performance dimension are we trying to move? (variance reduction / bias reduction / capacity / regularization)
- Default-params reference run: `runs/v{N}/<run_id>` with `cv_mean = ?`, `cv_std = ?`. Tuning budget justified only if default is already near feature-baseline-lift ceiling.

## 2. Parameter space (literature-informed)

Every parameter row MUST cite either a literature memo reference, a prior-version learning, or an explicit "first-pass default — no prior — treat as uninformative" note. No silent defaults.

| Param | Role | Range / Values | Scale (lin/log) | Literature / prior evidence | Expected direction of effect |
|---|---|---|---|---|---|
| learning_rate | step size | [0.01, 0.3] | log | LightGBM paper §3 | ↓ rate → ↑ trees but ↑ stability |
| num_leaves | capacity | [15, 255] | log | must satisfy `num_leaves < 2^max_depth` | ↑ leaves → ↑ capacity, ↑ overfit risk |
| min_data_in_leaf | regularization | [5, 200] | log | vN-1 saw overfit at 5 | ↑ → ↓ overfit |
| feature_fraction | regularization | [0.5, 1.0] | lin | — | <1 adds column-level bagging |
| ... | ... | ... | ... | ... | ... |

Exclusions (explicit): params we are NOT tuning this version, with reason (e.g., "objective=fixed-by-metric", "n_estimators=early-stopping-driven").

## 3. Strategy and stopping rules

- Strategy: <grid / random / bayesian / halving>. Justification: why this strategy matches the budget and param space.
- Early-stopping rule on trial level: stop trial if fold-1 CV < default_params_run CV − 1·cv_std.
- Early-stopping rule on search level: stop search if no trial has improved on rolling best over the last `k` trials (specify `k`).
- Multi-seed confirmation: top-3 configs by mean CV are re-run on `multi_seed` seeds; final chosen config must have `seed_std / tuning_lift_vs_default < 0.5` (otherwise treat as variance, not signal).

## 4. Nested-CV wiring (Iron Law #4)

Describe how inner folds are nested inside the outer folds — specifically how the hyperparameter selection for outer-fold `k` uses ONLY data from outer-folds `{1..K} \ k`. Any CV leak here silently inflates the tuning lift and is the single most common way tuning-as-p-hacking hides. The Skeptic MUST read and sign this section before execution.

## 5. Reporting contract

When tuning runs land on the leaderboard (via `scripts/tracker_log.py`), each row includes:

- `tuning_run: true`
- `parent_tuning_plan: tuning-plan-v{N}`
- `params: {the actual config}`
- `cv_mean`, `cv_std`, `cv_ci95`, `seed_std`, `seeds`
- `tuning_lift_vs_default: <cv_mean − default_cv_mean>` (signed, so "negative lift" is allowed and informative)
- `nested: true` (required — non-nested tuning runs are quarantined by the consistency linter)

## 6. Rejection criteria (pre-registered)

Tuning result is **rejected** if:
- `tuning_lift_vs_default` is within `default_run.cv_std`, OR
- the chosen config's `seed_std > 0.5 × tuning_lift_vs_default`, OR
- `nested: false` on any tuning run, OR
- any tuning run appears on the leaderboard without a parent `tuning-plan-v{N}` reference.

A rejection is NOT a failure — it is a disproven-card (`disproven/v{N}-dNNN.md`) documenting that the tuning budget did not produce learned signal above noise. This is the expected outcome of most tuning efforts and the reason we pre-register.

## 7. Plan updates log hook

On execution completion (whether accepted or rejected), append a revision block to `plans/v{N}-updates.md` at VALIDATE exit summarizing: number of trials run, best config, tuning_lift_vs_default, rejected-y/n, cost-in-minutes, what was learned for v(N+1).
