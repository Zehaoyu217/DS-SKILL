# Checklist: Leakage Audit

Run against `ds-workspace/src/` and `ds-workspace/nb/` at every FRAME, FEATURE_MODEL, and VALIDATE gate.

## Grep patterns (any hit = BLOCK)

| Pattern | Reason |
|---|---|
| `fit_transform\(.*\)` outside a sklearn `Pipeline` or `ColumnTransformer` applied via `cross_val_*` | Scaler/encoder fit on full data |
| `\.fit\([^)]*X[^)]*\)` called at module top-level or in a notebook cell | Fit-before-split |
| target-encoding logic (`groupby.*mean|agg`) computed on full data and joined pre-split | Classic target leak |
| Future-dated columns in features (names containing `next_`, `future_`, `label_t\+` ) | Time leak |
| Reading from `ds-workspace/holdout/` outside the ship gate | Holdout touch |

## Script
`scripts/leakage_grep.sh <path>` exits non-zero and prints hits.

## Persona output
Validation Auditor writes `ds-workspace/audits/vN-leakage.md` with PASS or BLOCK verdict.
