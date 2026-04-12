# Event: novel-modeling-flag

## Trigger
Proposed model family for v(N)'s FEATURE_MODEL is outside `{linear, tree, gbm}`. Flag set by orchestrator when `plans/vN.md` hypothesis names e.g. a neural net, transformer, state-space model, Bayesian hierarchical, causal model, etc.

## Immediate response (in order)
1. Print banner to user: `NOVEL MODELING FLAG — literature memo required before FEATURE_MODEL`.
2. Dispatch Literature Scout in Lite mode (Full if metric-plateau also active).
3. Gate FEATURE_MODEL entry on `literature/vN-memo.md` presence; refuse entry until memo exists.

## Required artifacts
- `literature/vN-memo.md` covering at least: prior Kaggle solutions for similar problem class, GitHub repos with >= 500 stars within 18 months, 2+ arXiv papers within 3 years, at least 1 mature PyPI package evaluated.

## Resolution criteria
Memo committed AND FEATURE_MODEL entry gate re-checks and finds the memo AND the chosen approach cites at least one memo source OR explicitly justifies deviating from memo recommendations.
