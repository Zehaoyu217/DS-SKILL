# Anti-Goodhart checklist (Iron Law #23)

Optimizing a single metric is the shortest path to reward hacking. This checklist
defines the *secondary metrics* — monitored but never optimized — that must be
declared at FRAME and checked at every ship-gate.

## When to run
- At FRAME: declare ≥2 secondary metrics in `plans/v1.md.pre_registration.secondary_metrics`
- After every run: log secondary values via `scripts/tracker_log.py`
- At ship-gate: refuse if any secondary has degraded >2σ from the feature-baseline's value

## Menu of secondary metrics

Pick ≥2 from the menu below (or add project-specific equivalents). The right pair
depends on the primary metric, the problem type, and the DGP-identified risks.

### Classification primary metrics (ROC-AUC, PR-AUC, F1, accuracy, log-loss)

| Metric | What it monitors | When to prefer |
|---|---|---|
| `calibration_ece` (Expected Calibration Error) | Probabilistic honesty — are predicted probabilities well-calibrated? | Any time probabilities are consumed by a downstream system |
| `worst_segment_score` | Worst-performing k% segment of the primary metric | Imbalanced populations, regulated domains, fairness-adjacent problems |
| `class_parity_gap` | Difference in primary metric across protected/demographic groups | Fairness-sensitive problems; flag when a feature improves primary but widens gap |
| `per_feature_importance_stability` | Jaccard of top-10 features across seeds | Guards against noise-chasing when seed-to-seed churn is high |
| `prediction_entropy` | Mean entropy of predicted distributions | Flags over-confident models; useful when downstream uses confidence to decide review |

### Regression primary metrics (RMSE, MAE, R², quantile loss)

| Metric | What it monitors | When to prefer |
|---|---|---|
| `residual_heteroskedasticity` | Is error variance a function of prediction magnitude? | When downstream consumers need consistent error bars |
| `tail_loss_p95` | Loss on the 95th-percentile-error slice | High-stakes regressions (finance, safety) where tail matters more than mean |
| `segment_worst_mae` | Worst-segment MAE | Segmented populations; flag when population mean improves but a group worsens |
| `prediction_bounds_respected` | % of predictions outside plausible range (negative counts, prices > cap) | When domain has hard constraints |

### Universal secondaries (useful for most problems)

| Metric | What it monitors | When to prefer |
|---|---|---|
| `coverage_of_test_distribution` | Fraction of test rows with no train-side near-neighbor | Guards against train/test drift becoming a shortcut |
| `train_test_loss_ratio` | `train_loss / test_loss` — overfit signal | Always useful; >3× is a loud warning |
| `seed_std_fraction` | `seed-to-seed std / cv_mean` | Stability across seeds; Iron Law #4 requires multi-seed, this surfaces the fragility |

## Pre-registration format

In `plans/v1.md.pre_registration`:

```yaml
secondary_metrics:
  - name: calibration_ece
    direction: min                   # min | max
    max_degradation_sigma: 2.0       # how much worse than feature-baseline is allowed at ship
    rationale: "This model's probabilities drive a downstream review-triage queue."
  - name: worst_segment_score
    direction: max
    max_degradation_sigma: 2.0
    rationale: "Segment X has < 1% of rows but drives 40% of decisions."
```

Changes after FRAME:
- **Adding** a secondary metric: allowed any time (strengthens the anti-Goodhart net).
- **Removing** a secondary metric: requires Iron Law #24 override `law=anti-goodhart-shrink`.
- **Relaxing `max_degradation_sigma`**: requires Iron Law #24 override.

## Ship-gate check

At SHIP, the ship-gate checklist (`checklists/ship-gate.md`) runs:

```
for each declared secondary_metric m:
  baseline_value = leaderboard.runs[where feature_baseline=true].secondary_metrics[m]
  candidate_value = leaderboard.runs[ship_candidate].secondary_metrics[m]
  delta = (candidate_value - baseline_value) / baseline_std_across_seeds
  if direction == 'min' and delta > max_degradation_sigma:  refuse ship
  if direction == 'max' and -delta > max_degradation_sigma: refuse ship
```

Refusal produces `audits/vN-anti-goodhart.md` with the delta table and a recommended
action (usually: pivot to a feature-subset that retains primary but restores the
secondary).

## Narrative audit hook (Iron Law #14)

`checklists/narrative-audit.md` is extended: any top-K feature that improves primary
but worsens any declared secondary must be acknowledged in
`audits/vN-narrative.md §4 "Goodhart risk"` with a justification. Unexplained cases
block ship.
