# ML Classification Patterns

Patterns specific to binary and multi-class classification problems.
Pull this up when setting up the evaluation framework, handling class
imbalance, or diagnosing segment-level performance disparities.

---

## Metric Choice for Imbalanced Data

**Worth exploring when:** Class imbalance is above 5:1; you are deciding
between PR-AUC, ROC-AUC, F1, log-loss, and accuracy as your primary
evaluation and optimisation metric; or different metrics are giving
conflicting signals about model quality.

**What to try:** Plot both the PR curve and the ROC curve for your best
baseline model. If positive-class precision at reasonable recall thresholds
matters for the downstream use case, PR-AUC is more informative than ROC-AUC.
Check what the ROC-AUC looks like on a trivial classifier (all negatives) —
if it is already above 0.85, ROC-AUC may be masking poor positive-class
performance.

**Ceiling signal:** Metric choice is locked and consistently applied across
all model evaluations; primary metric is clearly aligned with the downstream
decision the model will inform.

**Watch out for:** ROC-AUC is optimistic for imbalanced data — it rewards
correctly ranking the large negative class, even when precision on the minority
class is poor. PR-AUC forces you to confront the precision/recall trade-off
directly at the threshold that matters. For deployment, also consider what
the decision threshold will be: a model optimised for PR-AUC at FR=0.15 will
have different calibration requirements than one optimised for F1 at a fixed
threshold. Lock the metric before any modelling begins and do not change it
mid-project without re-evaluating all prior results.

---

## Class Imbalance Handling

**Worth exploring when:** Positive rate is below 20%; initial model has poor
recall on the minority class; you are considering oversampling (SMOTE),
undersampling, or class weighting to address the imbalance.

**What to try:** Establish an unweighted baseline first. Then test class
weighting (scale_pos_weight or class_weights proportional to inverse class
frequency) against the unweighted baseline on your primary metric. If using
log-loss or PR-AUC as primary metric, pay attention to calibration: plot the
predicted probability histogram for both classes. For severe imbalance (>20:1),
consider oversampling the minority class, but always test against the unweighted
baseline on held-out data.

**Ceiling signal:** Unweighted baseline and weighted variant tested; winner
identified on primary metric; probability calibration checked; further weight
or sampling variants add less than +0.001 on the primary metric.

**Watch out for:** Class weighting consistently hurts PR-AUC for moderate
imbalance in tree models — at 15% positive rate, class weights degraded OOF
by 0.011–0.014 across multiple model families and weight configurations.
Mechanism: weighting shifts probability calibration toward over-confident
positive predictions, reducing precision at all recall levels. Unweighted
log-loss produces well-calibrated probabilities which are optimal for PR-AUC.
SMOTE introduces synthetic samples that can confuse models about the true
decision boundary, especially for structured/tabular data where feature
combinations have physical meaning.

---

## Segment-Level Performance Analysis

**Worth exploring when:** Overall OOF has plateaued; domain suggests natural
subgroups (temperature regimes, geographic zones, time periods, user cohorts);
you suspect the model handles easy cases well but fails on a hard subgroup
that the aggregate metric obscures.

**What to try:** Stratify OOF predictions by high-importance categorical
features or binned continuous features. Compute your primary metric separately
for each stratum. Identify any segment with materially lower performance.
For that segment: check if domain knowledge suggests additional features
specific to it; try targeted feature engineering; consider whether a per-
segment ensemble (see ensemble patterns) could help.

**Ceiling signal:** All major segments show similar performance relative to
their expected difficulty; segment-specific improvement attempts have been
exhausted (3+ approaches tried); the bottleneck segment's performance has
not changed with targeted work.

**Watch out for:** Sometimes a segment is intrinsically harder — not because
of missing features, but because the underlying signal is weaker or noisier
for that subpopulation. In one project, a cold-temperature regime plateaued
at PR-AUC = 0.652 despite 40+ targeted attempts: specialist models trained
only on that segment, dedicated features, threshold flags, pseudo-labelling —
all failed or hurt. Recognising an intrinsic ceiling (vs a fixable bottleneck)
saves significant iteration time. Ask: does the bottleneck segment have fewer
labelled examples, noisier sensors, or a fundamentally different DGP? If yes,
it may be a data problem rather than a modelling problem.
