# Checklist: Encoding Audit

Target / mean / count / frequency / OOF-stack encoders are the highest-yield leak vectors in tabular ML. Run this checklist at every FEATURE_MODEL and VALIDATE gate, in addition to [leakage-audit.md](leakage-audit.md).

## Grep patterns (any hit = BLOCK until remediated)

| Pattern | Reason |
|---|---|
| `groupby\([^)]+\)\[["']?target["']?\]\.(mean\|sum\|count\|agg)` outside a function that receives `train_idx` / `val_idx` | Target statistic computed on full data |
| `category_encoders\.(TargetEncoder\|LeaveOneOutEncoder\|CatBoostEncoder)` without `cv=` or without being wrapped in `Pipeline` inside `cross_val_*` | Encoder fit outside fold |
| `df\[.*?\]\.map\(.*?target.*?\)` | Manual mean/target mapping |
| `pd\.factorize\(` on concatenated train+test before split | Category codes leak future categories |
| `OrdinalEncoder\(.*?\)\.fit\(pd\.concat` | Same |
| `rank\(` or `pct_rank` over full df before split | Rank leak |
| `\.cumsum\(\)` or `\.expanding\(\).(mean\|sum)` without an explicit time/group guard | Time leak via cumulative statistic |

## OOF-stacking audit (for ensembles)

- [ ] First-level OOF predictions are produced from a CV loop where each fold's prediction uses a model trained **only** on the other folds.
- [ ] Second-level (meta) model is trained on the OOF prediction matrix, not on in-fold predictions.
- [ ] Test-time predictions use first-level models re-fit on the full training set (or an averaged fold-model ensemble). Either choice is declared in `dgp-memo.md` §6 and kept consistent.
- [ ] No row in the OOF matrix was produced by a model that saw that row's target.
- [ ] If any first-level model uses its own CV (e.g., lightgbm with `early_stopping`), early stopping uses a *within-fold* validation split, not the outer OOF fold.

## Nested-CV audit (for any tuned hyperparameters)

- [ ] Hyperparameter search runs inside an outer CV fold, not on the full dataset.
- [ ] Reported `cv_mean`/`cv_std` comes from the **outer** fold metrics, not from the best inner search score.
- [ ] If a single tuning run on the full train set is used for speed, the `cv_mean` reported is discounted by at least the observed optimization bias on a held-out slice, and this is logged in `runs/vN/tuning-note.md`.

## Smoothing / regularization audit

- [ ] Target encoders use smoothing parameter >= 1 (documented choice).
- [ ] Rare-category handling: categories with count below threshold collapse to a shared bucket fit inside fold.
- [ ] Test-time unseen categories map to the global prior, not to NaN or a zero encoding.

## Persona output
Validation Auditor writes `ds-workspace/audits/vN-encoding.md` with Verdict [PASS | BLOCK] and lists hits with file:line. Any BLOCK fires `leakage-found` and invalidates affected runs.
