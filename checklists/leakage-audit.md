# Checklist: Leakage Audit

Run against `ds-workspace/src/` and `ds-workspace/nb/` at every AUDIT, FEATURE_MODEL, and VALIDATE gate. Pairs with [encoding-audit.md](encoding-audit.md) for encoder-specific leaks.

## Code-leakage grep patterns (any hit = BLOCK)

| Pattern | Reason |
|---|---|
| `fit_transform\(.*\)` outside a sklearn `Pipeline` or `ColumnTransformer` applied via `cross_val_*` | Scaler/encoder fit on full data |
| `\.fit\([^)]*X[^)]*\)` called at module top-level or in a notebook cell | Fit-before-split |
| target-encoding logic (`groupby.*mean\|agg`) computed on full data and joined pre-split | Classic target leak (see [encoding-audit.md](encoding-audit.md) for deeper checks) |
| Future-dated columns in features (names containing `next_`, `future_`, `label_t\+`) | Time leak |
| Reading from `ds-workspace/holdout/` outside the ship gate | Holdout touch |
| `pd\.concat\(\[train.*test\]\)` followed by `.fit(` or `.transform(` on aggregates | Fit on train+test concat |
| `.rolling\(.*\).(mean\|sum)` or `.expanding\(` without `min_periods` guard in time features | Rolling window leaks future |
| Second-level (stack) model fit on predictions produced from in-fold training data | OOF violation (see [encoding-audit.md](encoding-audit.md) stacking section) |
| Hyperparameter tuning function called without wrapping CV loop | Nested-CV violation |
| `pd\.read_.*\(.*submission.*\)` during training code path | Submission file read at train time (should only be read at predict time) |

## Structural-leakage checks (require DGP memo cross-reference)

- [ ] Every field in `src/features/` has an entry in `dgp-memo.md` §2 provenance table.
- [ ] No feature tagged `at-label` or `post-label` is used without written justification.
- [ ] Aggregations over groups (e.g., `user_mean_X`) respect the time boundary: aggregate only uses rows with label-event time earlier than the current row's label-event time. If no time, the group-wise mean is computed inside each CV fold.

## Script
`scripts/leakage_grep.sh <path>` exits non-zero and prints hits. Covers all code-leakage grep patterns above.

## Eval harness integrity check (Iron Law #20)

Run at FEATURE_MODEL entry, VALIDATE entry, and SHIP entry.

- [ ] Run `python $SKILL/scripts/hash_eval_harness.py ds-workspace --check`. Exit non-zero = BLOCK (`eval-harness-tampered` event).
- [ ] `data-contract.md` contains `eval_harness_sha256:` under `## Eval harness lock` with a non-placeholder value.
- [ ] The hash matches the current `src/evaluation/` `.py` file contents.

If the check fails, do not proceed. User must invoke `override eval-harness <reason>` to unlock and individually decide which affected runs remain valid.

## Persona output
Validation Auditor writes `ds-workspace/audits/vN-leakage.md` with PASS or BLOCK verdict. Any BLOCK fires `leakage-found` event and invalidates affected runs on the dashboard.
