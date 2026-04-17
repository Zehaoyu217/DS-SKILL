# Event: metric-plateau

## Trigger
Two consecutive vN complete FINDINGS with no statistically significant CV improvement (tested via Statistician using appropriate non-inferiority/improvement test). Dashboard `metric-over-time` chart flattens within `cv_std` band.

## Immediate response (in order)
1. Print banner to user: `METRIC PLATEAU — two vN without stat-sig gain`.
2. Force Full Literature Scout (not Lite) before v(N+1) can enter FEATURE_MODEL; block non-literature v(N+1) FEATURE_MODEL entry.
3. If this is the 3rd consecutive plateau vN, orchestrator proposes `ship` or `pivot` per Stop criteria in `loop-state-machine.md`.

## Required artifacts
- `literature/v(N+1)-memo.md` in Full mode covering: prior Kaggle solutions, GitHub repos, arXiv papers (all within recency windows), PyPI packages evaluated.
- Skeptic-signed decision note in `audits/v(N+1)-skeptic.md` choosing continue/pivot/ship with justification.

## Resolution criteria
Full Literature memo committed AND v(N+1) opens with at least one hypothesis sourced from the memo OR user invokes `ship`/`abort`.

## Resume phase
Orchestrator sets `state.current_v = N+1`, `state.current_phase = FRAME`, and re-enters `playbooks/phase-frame.md`. Literature Scout memo is a **prerequisite for FEATURE_MODEL entry** in v(N+1) — the FRAME gate may not close without it.
