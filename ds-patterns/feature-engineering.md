# Feature Engineering Patterns

Patterns for creating, encoding, and pruning features.
Pull this up when data quality is established and you are ready to explore
what new signals can be extracted from the raw columns.

---

## Domain and Physics Features

**Worth exploring when:** You have interpretable numeric columns and some
domain knowledge about how they interact (electrical, mechanical, thermal,
biological systems, etc.). Raw columns alone may not capture the physically
meaningful quantity.

**What to try:** Derive features from first principles — for example,
power dissipation = current² × resistance (Ohm's law), thermal resistance =
temperature_excess / power (°C/W), proximity to resonance =
1 / (|resonance_freq − operating_freq| + ε). After deriving, check permutation
importance: if the derived feature ranks above both raw components, it is
carrying independent signal.

**Ceiling signal:** New physics/domain features rank below the top 10 in
permutation importance for 3+ consecutive additions; adding further derived
features no longer improves OOF; the domain-explainable feature space is
exhausted.

**Watch out for:** Domain features are most valuable when the raw columns are
not directly interpretable by tree splits alone (non-linear combinations,
ratios with physical meaning). If a derived feature is highly correlated with
an existing raw column (r > 0.95), it adds little independent signal.
High-importance domain features are also good sanity checks: if ambient
temperature ranks #1 in importance for a thermal failure model, that confirms
the DGP memo prediction and builds confidence in the feature pipeline.

---

## Target Encoding Stability

**Worth exploring when:** High-cardinality categorical columns are present
(>20 unique values) and you suspect they carry failure-rate signal that tree
models are not capturing from the raw category labels.

**What to try:** Start with 5-fold CV-aware target encoding with a smoothing
parameter. Rule of thumb before applying: check that avg_count_per_category ≥
10 × smoothing_parameter. If using CatBoost, try the native cat_features
parameter (Ordered Target Encoding) before writing external TE code — it
eliminates fold leakage by construction and is worth comparing against
external TE as a baseline.

**Ceiling signal:** OOF no longer improves when adding TE for additional
categorical columns; permutation importance of TE features plateaus; all
high-cardinality categoricals have been evaluated.

**Watch out for:** Target encoding catastrophically overfits when
avg_count_per_category < 10× smoothing — one project observed OOF collapsing
from 0.70 to 0.45. Always verify the avg_count rule before applying TE to a
new column. CatBoost native Ordered TE consistently outperforms external
CV-aware TE for high-cardinality features (+0.0015 OOF at 1208 unique
categories). XGBoost and LightGBM native categorical handling are materially
weaker than CatBoost OTE for high-cardinality columns — do not assume all
tree frameworks handle categoricals equivalently.

---

## Interaction Terms — Threshold vs Soft

**Worth exploring when:** You suspect two features have a combined effect
stronger than their individual effects; domain knowledge suggests a threshold
behaviour (e.g., "above X temperature, degradation rate changes"); PDP analysis
has revealed a regime shift in a continuous feature.

**What to try:** Look for sharp thresholds first using PDP plots (see the
PDP-guided threshold discovery pattern). For any threshold found, create a
binary flag for the regime, then create a cross-product of that flag with the
interaction partner feature. Test whether OOF improves vs the baseline without
the interaction. Compare the regime flag alone vs the full interaction term.

**Ceiling signal:** 3+ explicit interaction combinations tried; none improve
OOF by more than +0.001; permutation importance of interaction features is
near zero.

**Watch out for:** Explicit interaction features only help when the interaction
has a SHARP THRESHOLD that trees find hard to discover through sequential splits.
Soft interactions (where both components vary continuously and their relationship
is smooth) are already captured by the tree's sequential splitting — adding
them explicitly adds noise and can hurt OOF by −0.002. If the interaction you
are thinking about is not threshold-shaped, it is probably not worth the
engineering cost.

---

## PDP-Guided Threshold Discovery

**Worth exploring when:** A continuous feature has high permutation importance;
you suspect it has a non-linear regime (a threshold above/below which failure
rate changes sharply); you want to check whether a binary flag would add signal
on top of the continuous feature.

**What to try:** Plot partial dependence (PDP) of top-ranked continuous features.
Look for sharp inflection points — places where the predicted outcome changes
rapidly over a narrow feature range. For any inflection found, create a binary
flag at that threshold value (e.g., `is_hot_regime = ambient_temp > 17.5`).
Test the flag alone and together with the raw feature; check OOF lift.

**Ceiling signal:** PDPs of all top features are roughly monotonic or smooth
curves with no sharp inflection; binary flags derived from any inflection points
add less than +0.001 OOF; all major continuous features have been inspected.

**Watch out for:** A PDP threshold that looks sharp in aggregate may be
confounded by another feature — the "regime" may actually be a proxy for a
different variable. Always check whether the threshold signal survives after
conditioning on likely confounders before engineering the flag. PDP is an
average effect and can mask heterogeneous subgroup behaviour.

---

## Permutation Importance Pruning

**Worth exploring when:** Feature set is large (>50 features); overfit delta
is elevated (>0.05, where overfit delta = in-sample metric − OOF metric);
new features have been added in recent versions that may be redundant or noisy.

**What to try:** Compute permutation importance on OOF predictions — shuffle
each feature and measure the drop in OOF metric. Sort ascending. Prune
features with negative importance first (they actively mislead the model);
then consider pruning near-zero features if overfit delta is elevated. Retrain
and verify that OOF improves and overfit delta falls.

**Ceiling signal:** No remaining features have negative importance; removing
any more features hurts OOF; overfit delta is below 0.05 and stable.

**Watch out for:** Negative-importance features are the highest-confidence
pruning targets — they consistently add +0.001 to +0.003 OOF when removed.
Features that appear in interaction terms may show low marginal importance but
high conditional importance — check interactions before pruning. Do not prune
features with low-but-positive importance unless overfit delta is your
primary concern; you may be removing genuinely weak but non-zero signal.
