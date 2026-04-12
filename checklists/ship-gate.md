# Checklist: Ship Gate

Final gate. Every box ticked, or no ship.

## Blockers
- [ ] Zero open CRITICAL findings from Skeptic, Validation Auditor, Statistician, Engineer.
- [ ] All HIGH findings resolved or explicitly waived in `audits/vN-ship-gate.md` with rationale.

## Metric
- [ ] CV metric meets pre-declared target (recorded in `plans/v1.md` framing, never moved).
- [ ] `cv_std` and `cv_ci95` present for the winning run.
- [ ] Lift vs baseline is statistically significant (Statistician-signed).

## Holdout read (the only one)
- [ ] Pre-compute predicted interval `cv_mean ± 2 * cv_std`.
- [ ] Read `ds-workspace/holdout/holdout.parquet` exactly once.
- [ ] Increment `state.holdout_reads` to 1 and stamp `audits/vN-repro.md`.
- [ ] If holdout metric is outside the predicted interval → fire `cv-holdout-drift`, do NOT ship.

## Reproducibility
- [ ] Engineer re-ran random-fold within tolerance.
- [ ] `env.lock`, `seed.txt`, `data.sha256` committed.

## Artifacts
- [ ] `report.md` generated: framing, CV results, holdout result, disproven-cards list, promotion candidates.
- [ ] `report.pdf` optional.
- [ ] Dashboard `leaderboard.json` shows the winning run with `status: valid` and no other run with a higher metric.

## Personas
All four: Skeptic + Validation Auditor + Statistician + Engineer. Every one must sign `audits/vN-ship-gate.md`.
