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

## Resume phase
Orchestrator resumes at `state.current_phase = FEATURE_MODEL` — the gate that was blocked. The literature memo is now a read-only input to the FEATURE_MODEL brainstorm.

---

# Event: novel-feature-flag

## Trigger
A feature engineering approach in the FEATURE_ENG brainstorm (`runs/vN/brainstorm-vN-FEATURE_ENG.md`) proposes a representation outside the standard set: `{raw, binned, log-transform, interaction, aggregation, categorical-encoding, embedding}`. Examples: graph neural network features, time-series spectral features, text embeddings from a fine-tuned model, survival-analysis-derived features, wavelet transforms.

Flag is set by the orchestrator when reviewing the FEATURE_ENG brainstorm at step 0.2 of FEATURE_MODEL.

## Immediate response (in order)
1. Print banner: `NOVEL FEATURE FLAG — literature memo required before implementing novel feature approach`.
2. If `literature/vN-memo.md` already exists in Full mode: verify it covers the novel approach. If so, proceed.
3. If memo is Lite or absent: dispatch Literature Scout in Full mode targeting the novel feature technique specifically.
4. Pause FEATURE_MODEL step 1 until memo is present.

## Required artifacts
- `literature/vN-memo.md` in Full mode with a section covering the novel feature technique (or an explicit "first-occurrence gap" note with rationale for why prior art is unavailable).

## Difference from novel-modeling-flag
`novel-modeling-flag` concerns the model family (what learns). `novel-feature-flag` concerns the feature representation (what the model receives). Both require Full lit memo, but they can co-occur. If both fire, one Full memo covering both is acceptable.

## Resolution criteria
Memo present in Full mode AND the FEATURE_ENG brainstorm alternative citing the novel technique references at least one memo source OR explicitly documents "no prior art found" with a search account.

## Resume phase (novel-feature-flag)
Orchestrator resumes at `state.current_phase = FEATURE_MODEL`, step 1 (the paused step). Memo becomes a read-only input to the FEATURE_ENG brainstorm.
