# Event: cv-holdout-drift

## Trigger
At ship gate, holdout metric falls outside the predicted interval `cv_mean ± k * cv_std` (default k=2) computed from the VALIDATE-phase `runs/vN/metrics.json`.

## Immediate response (in order)
1. Print banner to user: `CV-HOLDOUT DRIFT — do NOT ship`.
2. Increment `state.holdout_reads` (Iron Law #1 — the read is logged and tracked).
3. Record the drift in `audits/vN-repro.md` with observed vs. predicted intervals and drift magnitude.
4. Do NOT mark the run as shipped; invalidate the ship attempt on dashboard.
5. Close vN as incomplete; open v(N+1).
6. Prefill v(N+1) frame to investigate drift source (selection bias, temporal drift, group leakage, sampling difference).

## Required artifacts
- `audits/vN-repro.md` drift section documenting observed holdout metric, predicted interval, and delta.
- `plans/v(N+1).md` with drift-investigation hypothesis (e.g., "temporal distribution mismatch between train+CV and holdout").
- Dashboard entry marking the attempted ship as `invalidated: true`.

## Resolution criteria
Drift source identified AND either remediated in v(N+1) (new ship attempt) OR documented as an accepted limitation with Skeptic + Statistician sign-off in `audits/v(N+1)-skeptic.md`.
