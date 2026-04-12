# Phase: FEATURE_MODEL

## Entry gate
EDA exited AND at least one entry in `runs/*/metrics.json` tagged `baseline: true` exists. If `novel-modeling-flag` is active, also requires `literature/vN-memo.md`.

## Purpose
Implement features and models, run cross-validation, record metrics with uncertainty quantification, maintain leaderboard integrity, and confirm no new leakage patterns emerge during implementation.

## Steps (in order)
1. Implement features in `src/features/` and models in `src/models/` following the CV scheme from FRAME.
2. Run cross-validation and record results in `runs/vN/metrics.json` with fields: `cv_mean`, `cv_std`, `cv_ci95`, `lift_vs_baseline`, `baseline: false` (set to `true` only for baseline model).
3. Update `dashboard/data/leaderboard.json` via write-temp-then-rename atomically.
4. Append one JSON line event record to `dashboard/data/events.ndjson` (timestamp, run ID, event type).
5. Engineer sanity-check: verify presence of `env.lock`, `seed.txt`, `data.sha256` in `runs/vN/`.
6. Validation Auditor re-runs leakage audit [checklists/leakage-audit.md](../checklists/leakage-audit.md) on new code in `src/`.

## Persona invocations
- **Engineer** (primary): Implement features/models, run CV, populate metrics, record seed/env/hash. Output: code in `src/`, metrics in `runs/vN/metrics.json`.
- **Validation Auditor** (mid-phase): Re-grep `src/` for leakage patterns on new code. Output: findings in `audits/vN-leakage.md` (update from AUDIT phase).
- **Literature Scout** (if `novel-modeling-flag` active and memo not yet present): Produce `literature/vN-memo.md`.

## Exit gate
Current run present in `leaderboard.json` (Iron Law #11) AND no active leakage patterns found. Metrics include `cv_std` or `cv_ci95`.

## Events that can abort this phase
- `leakage-found` (Validation Auditor grep hits a new pattern; mark runs invalidated and open v(N+1))
- `novel-modeling-flag` (if not yet flagged and fires now; require literature memo before continuing)
