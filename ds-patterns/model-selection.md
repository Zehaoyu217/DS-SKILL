# Model Selection Patterns

Patterns for choosing model architecture, tuning regularization,
handling categoricals, and diagnosing calibration issues.
Pull this up when training your first model, when overfit delta is elevated,
or when considering a different model family.

---

## Tree Depth and Regularization Tuning

**Worth exploring when:** You are training your first model for a dataset
(establish the regularization baseline), or overfit delta is above 0.05
(in-sample metric minus OOF metric), or OOF has plateaued after feature
changes and you haven't revisited depth/regularization recently.

**What to try:** Use overfit delta as a compass throughout tuning — high delta
signals under-regularization. Try reducing max_depth (CatBoost) or num_leaves
(LightGBM) by 1–2 steps and observe both OOF and overfit delta together. For
CatBoost, also try increasing l2_leaf_reg. For LightGBM, try increasing
min_child_samples and lambda_l2. Track each step: if OOF improves and delta
falls, continue in that direction.

**Ceiling signal:** Overfit delta is stable below 0.05; further regularization
starts hurting OOF without reducing delta; 4+ depth/regularization configs
tried with diminishing returns.

**Watch out for:** Overfit delta and OOF can be anti-correlated at Pearson
r ≈ −0.95 across regularization steps — every step tends to improve OOF, right
until a clear plateau. The plateau is the real ceiling, not any fixed delta
value. Each model family has its own optimal depth: CatBoost may be optimal at
depth=5 where LightGBM is optimal at num_leaves=11 — don't assume configurations
transfer between families. Shallow trees tend to reward smooth data-generating
processes; if your DGP is complex and jagged, very shallow may not be optimal.

---

## Native Categorical Encoding Comparison

**Worth exploring when:** High-cardinality categorical columns are present and
you are choosing between model families, or you are deciding between external
target encoding and native model handling.

**What to try:** For CatBoost, pass high-cardinality columns via cat_features
for native Ordered Target Encoding — this is worth trying before writing
external TE code. For XGBoost, try enable_categorical=True. For LightGBM,
try categorical_feature. Compare OOF for each option against a baseline with
external CV-aware TE. Run each variant with the same seed to isolate the
encoding effect.

**Ceiling signal:** All encoding variants have been tested; winner identified;
additional encoding combinations return less than +0.001 OOF difference.

**Watch out for:** CatBoost native OTE is consistently the strongest option
for high-cardinality categoricals — it eliminates fold leakage by using an
ordered boosting sequence. XGBoost native categorical handling was materially
weaker (−0.021 OOF vs CatBoost) and LightGBM native was even weaker (−0.037
OOF vs CatBoost) in one comparison at 1208 unique categories. External CV-aware
TE fell in between but still below CatBoost OTE. Also note: XGBoost
enable_categorical=True requires explicit float32 DataFrame construction —
mixing numpy arrays causes all columns to silently become object dtype and the
encoding fails silently.

---

## Class Weighting and Metric Alignment

**Worth exploring when:** Dataset has class imbalance (positive rate < 30%);
you are considering scale_pos_weight (XGBoost), class_weights (CatBoost), or
sample_weight arrays to address the imbalance; or initial model performance on
the minority class looks poor.

**What to try:** First establish an unweighted baseline. Then test one variant
with class weights proportional to inverse class frequency. Compare both on
your primary metric. If your primary metric is threshold-free (PR-AUC,
ROC-AUC, log-loss), pay particular attention to calibration — plot predicted
probability distributions for both classes.

**Ceiling signal:** Tested unweighted vs weighted; winner identified clearly
on primary metric; probability calibration checked; further weight variants
add less than +0.001.

**Watch out for:** Class weighting consistently hurts PR-AUC for moderate
imbalance — at a 15% positive rate, adding class weights degraded OOF by
0.011–0.014 across CatBoost, XGBoost, and multiple weight configurations. The
mechanism: weighting shifts probability calibration toward over-confident
positive predictions, reducing precision at all recall thresholds. Unweighted
log-loss produces well-calibrated probabilities, which are already optimal for
threshold-free metrics like PR-AUC. This is counter-intuitive — adding weight
to the minority class feels correct but empirically backfires for PR-AUC
optimisation at moderate imbalance.

---

## Non-Tree Models on Engineered Features

**Worth exploring when:** You want blend diversity beyond tree families;
considering MLP, ExtraTrees, or other gradient-based architectures; current
tree-based ceiling has been reached.

**What to try:** If your features were engineered for tree models (binary
threshold flags, ordinal encodings, categorical aggregates), first try the
non-tree model on raw or minimally processed features — not the tree-optimised
feature set. Normalise continuous features. Consider a separate feature
preparation branch for non-tree models.

**Ceiling signal:** Non-tree model OOF is within 0.02 of tree baseline on
either tree-optimised or raw features; or 2+ non-tree architectures tried with
similar underperformance.

**Watch out for:** Non-tree models (MLP, ExtraTrees) trained on tree-optimised
feature sets performed approximately 0.10 OOF below the tree baseline in one
project — the binary flags, ordinal encodings, and categorical aggregates
contained implicit tree-split assumptions that confused gradient-based models.
If you want neural network diversity in an ensemble, prepare features
independently for the non-tree model rather than reusing the tree-optimised
pipeline. Expect lower individual OOF but potentially useful error diversity
for blending.
