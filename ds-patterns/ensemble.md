# Ensemble Patterns

Patterns for building, selecting, and diagnosing model ensembles.
Pull this up when a single model family has been tuned to its ceiling,
when you are deciding how to combine a pool of candidates, or when blend
scores have stopped improving.

---

## Cross-Family Diversity Before Same-Family Variants

**Worth exploring when:** You have tuned one model family (e.g., CatBoost)
and want to push beyond its single-model ceiling; you have not yet tried
models from other tree families.

**What to try:** Before adding more hyperparameter variants within your best
family, add one well-tuned model from each other major tree family (CatBoost,
XGBoost, LightGBM). Even if the other families produce individually weaker
models, their error patterns may be sufficiently uncorrelated to provide
meaningful blend lift. Use Caruana greedy selection to let the ensemble choose
which models contribute.

**Ceiling signal:** One model from each major tree family has been included;
cross-family blend OOF has plateaued; adding further same-family variants
no longer improves blend.

**Watch out for:** Cross-family diversity typically adds +0.003 to +0.006 OOF
over the best single model — considerably more than same-family hyperparameter
tuning. Spending 20 runs tuning CatBoost seeds before trying a single XGBoost
is a common mistake. Same-family variants produce highly correlated errors; the
blend gain from them is close to zero until a genuinely different architecture
is introduced. Blend OOF gains should be confirmed across ≥2 seeds before
concluding that a model adds meaningful diversity — single-seed blend results
can be noise, especially for gains below +0.002.

---

## Caruana Greedy vs Weight Optimisation

**Worth exploring when:** You have a pool of 10+ candidate models and are
deciding how to weight them; considering scipy L-BFGS-B or gradient-based
weight optimisation; pool is dominated by one architecture family.

**What to try:** Start with Caruana greedy ensemble selection (greedy
hill-climbing that adds one model at a time based on OOF metric improvement,
with replacement). On pools where one architecture dominates (>70% same
family), Caruana naturally caps the contribution of correlated models. Compare
greedy selection against equal-weight mean as a further baseline.

**Ceiling signal:** Caruana selected set is stable across 3+ pool updates;
OOF improvement from re-running selection is less than +0.001; adding new
models to the pool does not change the selected set.

**Watch out for:** Scipy/gradient-based weight optimisation tends to overfit
weight selection on correlated pools — Caruana greedy is more robust and
interpretable. Feature-bagging diversity (training models on random subsets
of features) can produce high internal OOF spread but Caruana selected none
of 15 feature-bagged models in one experiment — high diversity in prediction
spread does not guarantee useful ensemble contribution. A model must have
genuinely different error patterns, not just different variance, to be selected
by Caruana.

---

## Per-Segment Ensemble

**Worth exploring when:** Segment-level performance analysis reveals
heterogeneous regimes (e.g., one segment has metric 0.95, another has 0.65);
global ensemble OOF has plateaued for many versions; you have confirmed that
the segment difference is not just sample size (smaller segment is genuinely
harder).

**What to try:** Run Caruana greedy selection separately for each segment using
OOF predictions filtered to that segment's rows. For each segment, select the
best ensemble from the full pool. Combine by routing each test row to its
segment's ensemble for the final prediction.

**Ceiling signal:** Per-segment blend improvement over global blend is less than
+0.0002; segments do not differ materially in performance; segment-level
selection returns the same models as global selection.

**Watch out for:** Per-segment ensembles can break global pool saturation —
in one project, a +0.0004 OOF gain came from per-segment Caruana after 40+
versions of no global progress. However, training specialist models exclusively
on one segment's data (as opposed to selecting from globally-trained models)
can HURT that segment's performance — global models see more data for
calibration. Prefer selecting from globally-trained models per-segment rather
than training segment-specific models from scratch.

---

## Pool Saturation Signals

**Worth exploring when:** You have been adding models to the blend pool for
several versions with no OOF improvement; suspecting the pool is saturated
with models that produce too-similar errors.

**What to try:** Examine which models Caruana is actually selecting in its
final set — if the selected set has been identical across the last 3+ pool
updates, the pool is saturated with the current architecture family. Check the
OOF correlation matrix for the models in the pool: high average pairwise
correlation (> 0.95) confirms saturation. The path forward requires genuinely
different error patterns: a different model family, a new feature class that
changes prediction behaviour, or a per-segment approach.

**Ceiling signal:** Caruana selected set is identical across the last 3 pool
updates; OOF pairwise correlation of pool models is above 0.95 on average; all
approaches that were expected to add diversity have been tried.

**Watch out for:** Adding more same-architecture variants (more CatBoost seeds,
more hyperparameter combinations) rarely breaks pool saturation — the prediction
errors are too correlated for Caruana to prefer them. The only reliable
saturation-breaking approaches observed are: (a) a genuinely different model
family producing materially lower individual OOF but different errors,
(b) a new feature representation class that changes which examples the model
gets wrong, (c) per-segment ensemble architecture. If none of these are
available, the pool may be at its practical ceiling for the current feature set.
