# Checklist: Adversarial Validation

Train a binary classifier to distinguish training rows (label 0) from hidden-test / held-out rows (label 1). The resulting AUC measures how different the two distributions are. Run at AUDIT phase exit. Required by Iron Law #13.

## Protocol

1. Load train features and test features from `data/` (features only — never peek at test targets).
2. Concatenate with an `is_test` label column. Drop the original target from train.
3. Fit a GBM (lightgbm / xgboost) with 5-fold stratified CV on `is_test`.
4. Record:
   - `adv_auc`: mean CV AUC.
   - `adv_top_features`: top-10 features by split importance.
   - Per-feature single-column adv-AUC (train a classifier on each column alone; flag features with AUC > 0.55).
5. Duplicate detection:
   - Exact duplicates: `df.duplicated(subset=FEATURE_COLS)`. Log count.
   - Near-duplicate: fit a fast NN index on feature rows; for each test row find nearest train row; report `dup_ratio = fraction with distance < threshold` (threshold documented in memo).

## Interpretation and gates

| adv_auc range | Interpretation | Required action |
|---|---|---|
| 0.50 – 0.55 | Train/test indistinguishable | None. Record and continue. |
| 0.55 – 0.60 | Mild drift | Document drift features in `audits/vN-adversarial.md`. CV scheme may stay as-is if scheme already stratifies on these features. |
| 0.60 – 0.75 | Real drift | Fire `covariate-shift` event. Revise CV scheme before FEATURE_MODEL: time split, group split, or stratify-on-drift. Consider removing the top offending feature or transforming it. |
| > 0.75 | Train and test are near-disjoint populations | BLOCK. This is a fundamental problem. Reopen FRAME: the hidden test may be measuring something different from what the training set captures. |

| dup_ratio | Required action |
|---|---|
| > 0.05 | Remove duplicates from train, or weight them down, before CV. Document in audit. |
| > 0.20 | Fire `covariate-shift` event. Duplicates between train and test inflate CV in a way that will not generalize. |

## Output artifact
`ds-workspace/audits/vN-adversarial.md`:

```markdown
# Adversarial Validation vN
Reviewer: Validation Auditor
Date: <ISO>
adv_auc: <x.xxx>  (CV std: <y.yy>)
Top drift features: [...]
Exact dup count: <n> / <total>  (dup_ratio: <r>)
Near-dup (threshold=<t>): <n>
Verdict: [PASS | COVARIATE-SHIFT | BLOCK]
Required CV scheme update: <yes/no — specifics>
Sign-off: yes/no
```

## Inputs to downstream phases
`adv_auc` and `dup_ratio` are consumed by the expanded gap formula in VALIDATE (Iron Law #13):
`predicted_interval = cv_mean ± (2·cv_std + λ·max(0, adv_auc - 0.5) + μ·dup_ratio)`
Default λ = 0.2, μ = 0.3. Adjust per problem, document in `plans/vN.md`.
