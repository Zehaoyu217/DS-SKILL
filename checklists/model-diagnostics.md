# Checklist: Model Diagnostics

"A model is an information source, not just a score." Iron Law #18. Run after every candidate model in FEATURE_MODEL, before VALIDATE. The goal is to understand *how* the model works and *where* it fails — not just whether its score beats the baseline.

## Inputs
- Trained model from `runs/vN/`
- Validation fold predictions (out-of-fold or held-out CV predictions)
- `dgp-memo.md` §7a (pre-registered expected feature directions)
- Feature matrix and target variable

## 1. Interpretability toolkit

Run ALL of the following. They answer different questions and complement each other.

### 1a. SHAP values (global + local)
- Compute SHAP values on the validation set (TreeExplainer for tree models, KernelExplainer or LinearExplainer as appropriate).
- **Global**: SHAP summary plot (beeswarm or bar). Record top-20 features by mean |SHAP|.
- **Local**: For the 3 highest-confidence and 3 lowest-confidence predictions, produce SHAP waterfall or force plots.
- Save to `runs/vN/plots/shap_summary.png`, `runs/vN/plots/shap_local_*.png`.

### 1b. Partial Dependence Plots (PDP)
- For each of the top-10 features by importance: compute 1D PDP.
- For the top-3 suspected interaction pairs (from DGP memo §4 confounds or EDA hypotheses): compute 2D PDP.
- **Direction check**: compare PDP slope direction against DGP §7a expected directions. Non-monotonic PDP on a feature predicted to be monotonic is a HIGH finding (same check as narrative audit, but done earlier to catch issues before VALIDATE).
- Save to `runs/vN/plots/pdp_*.png`.

### 1c. Individual Conditional Expectation (ICE) plots
- For each of the top-5 features: overlay ICE curves on the PDP.
- **Heterogeneity check**: if ICE curves diverge significantly (high variance around PDP), the feature's effect is heterogeneous across subpopulations — flag for segment-level investigation in §2.
- Save to `runs/vN/plots/ice_*.png`.

### 1d. Permutation importance
- Compute permutation importance (≥5 repeats) on the validation set.
- Compare ranking against SHAP-based ranking. Large discrepancies (feature ranks differ by >5 positions) suggest: multicollinearity (SHAP splits credit, permutation doesn't), or interaction effects (SHAP captures interactions, permutation doesn't in isolation).
- Record both rankings side-by-side in `audits/vN-model-diagnostics.md`.

## 2. Segment-level weakness analysis

The overall CV metric hides subpopulation performance. A model can score well on average while systematically failing on a segment that matters.

### 2a. Continuous feature segments
- For each of the top-10 features (by importance): bin into 5 quantiles.
- Compute validation metric per bin.
- Flag bins where metric drops >1σ below the overall metric.
- For each flagged bin, investigate:
  - Is this a data sparsity issue? (few samples in the bin → high variance, not real weakness)
  - Is this a genuine model weakness? (adequate samples, consistently poor) → candidate for targeted feature engineering or a segment-specific model
  - Is this a confounding variable? (the flagged segment correlates with an unmeasured variable that the model cannot capture)

### 2b. Categorical feature segments
- For each categorical feature with ≤50 categories: compute validation metric per category.
- Flag categories where metric drops >1σ below overall AND sample size is adequate (≥30 rows or ≥1% of data).
- Same investigation questions as 2a.

### 2c. Cross-segment interactions
- For the top-2 flagged segments from 2a/2b: check if weakness persists when the segment is further sliced by the second most-important feature. This tests whether the weakness is truly about that segment or about an interaction.

### 2d. Residual analysis
- Plot residuals vs. predicted values. Check for heteroscedasticity or systematic patterns.
- Plot residuals vs. each of the top-5 features. U-shaped or curved residual patterns suggest missing nonlinearity or interaction terms.
- For classification: plot calibration curve (reliability diagram). Overconfident models (predicted probabilities far from observed frequencies) need recalibration.

## 3. Diagnostic-to-action mapping

Every diagnostic finding must map to an action:

| Finding | Possible actions |
|---|---|
| PDP direction contradicts DGP §7a | Write disproven-card against the DGP prediction; investigate root cause; possibly revise DGP memo in v(N+1) |
| ICE heterogeneity on feature X | Add interaction term X × Y (where Y is the suspected moderator); or split model by segment |
| Permutation importance ≫ SHAP importance for feature X | Investigate multicollinearity; consider dropping correlated features |
| Segment weakness in bin Q5 of feature X | Add features that capture what makes Q5 different; or add Q5-specific interaction terms; or document as known limitation |
| Calibration curve shows overconfidence | Apply Platt scaling or isotonic regression; document in findings |
| Residual pattern vs. feature X | Add polynomial or spline term for X; or add interaction with suspected moderator |

## Output
Write `audits/vN-model-diagnostics.md` with:
- Interpretability summary (top features by SHAP, permutation, PDP direction checks)
- Segment weakness table (flagged segments, metric drop, sample size, investigation outcome)
- Action items (what to try in the next iteration or feature engineering pass)
- Plots inventory (list of all diagnostic plots saved to `runs/vN/plots/`)

## Mode differences
Identical in competition and daily modes. Understanding the model is never optional.
