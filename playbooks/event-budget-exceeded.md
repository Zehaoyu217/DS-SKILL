# Event: budget-exceeded

## Trigger
`scripts/budget_check.py <ds-workspace> --account <run_id> --vN <N> --cost ...`
exits 3, indicating at least one envelope dimension (compute_hours,
api_cost_usd, wall_clock_days, max_versions, or max_runs_per_version) has
gone to ≤ 0. The script appends a `budget-exceeded` entry to
`state.events_history` (idempotent by v + exhausted dimensions).

## Immediate response (in order)
1. **Freeze new runs.** Orchestrator refuses to start another run until the
   event is resolved; cached runs in flight may complete so the ledger
   reflects true spend.
2. Read `budget.json` and identify which dimension(s) tripped the threshold
   (printed by `budget_check.py` and present in `state.events_history[-1].ref`).
3. Dispatch **Engineer** as an independent subagent to classify the overrun:
   - **Legitimate exploration** — hyperparameter sweeps, ensemble screening,
     additional CV folds requested by a gate. Recoverable via override.
   - **Accidental blow-out** — stuck training loop, infinite retry, dataset
     misload. Fix the code; do not override.
   - **Envelope mis-sized** — the FRAME-declared envelope was unrealistic
     given the problem size. Resize at the next version boundary.
4. Dispatch **Skeptic** to check whether the current leaderboard's best run
   already satisfies ship criteria. If yes, propose early SHIP rather than an
   override.

## Remediation paths

### Path A — Legitimate overrun, Iron Law #24 override
- Author `overrides/vN-override-budget.md` using
  [templates/override-card.md](../templates/override-card.md) with:
  - `law: budget`
  - `scope: run | version` (PERMANENT IS NOT PERMITTED — `signed_by` MUST
    always include `user` for law=budget regardless of mode; in autonomous
    mode this always escalates per
    `autonomous.yaml.escalate_to_human.budget_exhausted_before_ship`).
  - `expected_risk`: quantify the additional spend requested.
  - `mitigation`: what spend reductions compensate (fewer seeds, shorter
    early-stopping, cheaper model family for the next run).
  - `signed_by: [user, ...]`
- Update `budget.json.overrides_applied` with the override id.
- Do **not** edit `budget.json.envelopes` — leave the cap, log the overrun
  in the ledger, and let future runs see the persistent over-shoot.

### Path B — Accidental blow-out, fix + retry
- Engineer identifies the bug and commits a fix.
- Before the next run, call `scripts/budget_check.py --check` to confirm
  current status; note in step-journal.
- NO override needed (the event stands in events_history as a historical
  record, not a blocker, because the next run will be within envelope).

### Path C — Envelope mis-sized
- At the next vN boundary (after the current run completes / fails), write
  a scope=version override-card explaining the resize, append to
  `budget.json.overrides_applied`, and edit
  `budget.json.envelopes.<dimension>` to the new cap.
- Add a Meta-Auditor trigger: after two consecutive envelope resizes,
  `escalate_to_human.meta_auditor_critical_finding` fires.

### Path D — Autonomous-mode auto-defeat (Iron Law #22)
- In autonomous mode, if the Council does NOT approve a budget override AND
  no code fix is available, orchestrator proceeds to auto-defeat:
  1. Dispatches Meta-Auditor per
     [personas/meta-auditor.md](../personas/meta-auditor.md).
  2. On PASS: writes `disproven/surrender-vN.md`, sets
     `state.phase = ABORTED`, stops.
  3. On BLOCK: escalates per
     `escalate_to_human.budget_exhausted_before_ship`.

## Required artifacts
- Path A: `overrides/vN-override-budget.md` + updated
  `budget.json.overrides_applied` + `state.active_overrides` entry.
- All paths: step-journal entry linking to the `budget-exceeded` event and
  the chosen path.

## Resolution criteria
Either:
- `budget_check.py --check` exits 0 (envelope no longer exhausted — path B
  or C), OR
- `state.active_overrides` contains a valid `law=budget` override AND
  `consistency_lint.py` exits 0 AND the override's `expires_at` is in the
  future (path A), OR
- `state.phase = ABORTED` with a `disproven/surrender-vN.md` card (path D).

## Events this can chain into
- `auto-defeat` — path D terminal case.
- `meta-audit-triggered` — after two consecutive envelope resizes or before
  path D defeat.
- `override-activated` — when path A's override is filed.

## Dashboard
Ship-gate dashboard panel displays the current envelope remaining on every
dimension plus all `law=budget` overrides in chronological order.
`budget_check.py` writes a per-run ledger at
`runs/vN/<run_id>/budget-ledger.json` for post-mortem reconstruction.

## Resume phase
- **Path A (override):** resume at `state.current_phase` (unchanged) with the new override in `state.active_overrides`.
- **Path B (code fix):** resume at `state.current_phase` after the fix; the event stays in `events_history` as a historical record.
- **Path C (envelope resize):** current run completes/fails, then at the vN boundary orchestrator sets `state.current_v = N+1`, `state.current_phase = FRAME`, and applies the resized envelope.
- **Path D (auto-defeat):** `state.phase = ABORTED`, no further phase entry. Terminal.
