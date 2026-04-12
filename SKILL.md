---
name: data-science-iteration
description: Use when working from a dataset or model-with-data goal; runs a suspicious-yet-creative iterative loop (v1 → v2 → v3 …) with gated phases, persona sign-offs, locked-holdout discipline, literature review, disproven-as-artifact, and a live leaderboard dashboard.
---

# Data Science Iteration

## The Iron Law

```
NO PHASE TRANSITION WITHOUT A SIGNED GATE.
NO MODELED RUN OFF THE DASHBOARD.
THE LOCKED HOLDOUT IS READ EXACTLY ONCE, AT SHIP.
```

See [iron-laws.md](iron-laws.md) for the full list and enforcement mechanics.

## When to Use

- Starting a modeling project from data or a loose goal.
- When discipline matters more than speed (research, high-stakes decisions, reproducible science).
- When the decision/metric is roughly known. If it isn't, brainstorm the framing first with the user, then enter this skill.

## When NOT to Use

- Production MLOps, deploy, drift monitoring.
- AutoML bandits.
- Pure engineering tasks that happen to touch data.

## Entry flow

1. Ask four framing questions, one at a time:
   1. What decision does this model support? (grounds metric)
   2. Data unit/grain and time structure? (grounds CV scheme)
   3. Hard success threshold? (grounds ship gate)
   4. Track: notebook or script?
2. Create `ds-workspace/` using [workspace-layout.md](workspace-layout.md).
3. Seed dashboard from `dashboard-template/`. Start server via `server/serve_dashboard.py`. Print URL.
4. Draft `plans/v1.md` from `templates/plan-vN.md`.
5. Run Skeptic + Validation Auditor gate on the draft.
6. Enter loop: see [loop-state-machine.md](loop-state-machine.md).

## Loop (summary)

Phases per vN: `FRAME → AUDIT → EDA → FEATURE_MODEL → VALIDATE → FINDINGS → (SHIP | NEXT_V)`.
Events can abort and open vN+1 mid-phase — see [loop-state-machine.md](loop-state-machine.md).

## Personas and who gates what

See [personas/](personas/). Quick map:

| Gate | Required sign-off |
|---|---|
| FRAME exit | Skeptic + Validation Auditor |
| FEATURE_MODEL entry | baseline recorded + literature memo if novel-modeling-flag |
| VALIDATE exit | Statistician + Validation Auditor |
| FINDINGS exit | every hypothesis resolved to finding-card or disproven-card |
| SHIP | Skeptic + Auditor + Statistician + Engineer + ship-gate checklist |

## Parallel subagent dispatch at gates

For heavy reviews (Literature Scout full memo, multi-file leakage grep, reproducibility re-run), dispatch each persona as a parallel subagent. Each returns its audit artifact; orchestrator collects, then decides gate outcome.

## Dashboard contract

Every modeled run must appear in `ds-workspace/dashboard/data/leaderboard.json` before its phase can exit. See [dashboard-spec.md](dashboard-spec.md).

## User commands during loop

- `status` — print current phase, blockers, leaderboard top-3.
- `ship` — open ship-gate sequence.
- `abort` — tear down; dashboard preserved.
- `force v+1 <reason>` — close vN early and open v(N+1).
- `dig <hypothesis>` — branch investigation without leaving current vN.

## Red Flags (stop and check)

| Thought | Reality |
|---|---|
| "Let me just peek at the holdout" | Iron Law #1. Any unlogged read invalidates the run. |
| "CV scheme is obvious, skip the audit" | Iron Law #2. Time/group/stratified choice is signed before features. |
| "Fit the scaler on all data for convenience" | Iron Law #3. Fit inside folds only. |
| "Point estimate is fine" | Iron Law #4. CI or CV-std required. |
| "Baseline is boring, go straight to GBM" | Iron Law #5. Baseline first, always. |
| "This hypothesis didn't pan out, move on" | Iron Law #6. Write the disproven-card. |
| "This model is novel but I know the space" | Iron Law #7. Literature Scout memo committed first. |
| "t-test, run it" | Iron Law #8. Assumption tests first. |
| "Works on my machine" | Iron Law #9. Seed + env + data hash logged. |
| "Quick fit in the notebook cell" | Iron Law #10. Notebooks call `src/` only. |
| "Didn't log that run" | Iron Law #11. Not on dashboard = doesn't exist. |

## Compatibility (optional)

This skill is standalone. It is compatible with but does not require: `superpowers:brainstorming`, `python-patterns`, `python-testing`, `eval-harness`, `exa-search`, `deep-research`, `continuous-learning`. See spec §9.
