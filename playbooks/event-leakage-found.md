# Event: leakage-found

## Trigger
Any hit in `checklists/leakage-audit.md` grep sweep over `ds-workspace/src/` or `ds-workspace/nb/`, OR manual finding by any persona. Exact grep patterns: `fit_transform`, `.fit(X_train)` outside a Pipeline context, target encoding without CV, scaler fit on concatenated train+test.

## Immediate response (in order)
1. Print banner to user: `IRON LAW #3 VIOLATED — leakage found at <file:line>`.
2. Mark every run that touched the offending code `invalidated: true` in `dashboard/data/leaderboard.json` (atomic write) and append invalidation event to `events.ndjson`.
3. Close current vN as incomplete; open v(N+1) with remediation hypothesis prefilled.
4. Require fresh baseline run in v(N+1) before FEATURE_MODEL can exit.

## Required artifacts
- `audits/vN-leakage.md` with the offending lines, context, and fix applied.
- `plans/v(N+1).md` with remediation hypothesis H-v(N+1)-01 that directly addresses the leak.
- Fresh baseline entry in `runs/v(N+1)/metrics.json` tagged `baseline: true` (re-baseline required).

## Resolution criteria
Leakage grep clean (no hits on repaired code) AND re-baseline present AND Validation Auditor signs new `audits/v(N+1)-leakage.md` with Verdict=PASS.
