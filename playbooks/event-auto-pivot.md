# Event: auto-pivot

## Trigger
`state.plateau_streak >= autonomous.yaml.autonomy.plateau_threshold` (default
3). Plateau = no stat-significant CV-mean improvement over the prior version,
tested with Welch's t on seed-mean leaderboard entries. Orchestrator computes
this at VALIDATE exit and increments `plateau_streak` before checking the
threshold.

Fires only when `state.autonomous == true`. Interactive mode emits the
equivalent `audits/vN-pivot-proposal.md` and waits for user command — no
event.

## Immediate response (in order)
1. **Freeze FEATURE_MODEL / VALIDATE** work on current vN — no more runs at
   this version after the plateau-triggering run has been logged.
2. Read `coverage.json`; compute `candidate_areas` as:
   ```
   [area for area in coverage.pattern_areas
    if not area.exhausted
    and area.remaining_leverage_estimate > 0.2
    and area.id not in recent 3 areas tried (anti-thrash)]
   ```
   Rank by `autonomous.yaml.autonomy.pivot_priority_order` (stable sort;
   priority order is the tiebreaker, not the primary key).
3. If `candidate_areas` is empty → this is NOT a pivot; fall through to
   [event-auto-defeat.md](event-auto-defeat.md).
4. Dispatch **Explorer** as an independent subagent with the top-ranked
   area as focus prompt. Explorer seeds the brainstorm with ≥3 candidates
   specific to that pattern area. Its output is
   `runs/v(N+1)/brainstorm-v(N+1)-<area>.md`.
5. Dispatch **Skeptic** to micro-audit the pivot decision: is the plateau
   real (not within-noise)? Is the chosen area genuinely different from what
   was just tried? Skeptic writes a sign-off in
   `audits/vN-pivot-decision.md` §Skeptic review.
6. Open `v(N+1)` with the brainstorm as the FEATURE_MODEL pre-seed.
7. Reset `state.plateau_streak = 0`. Leave
   `state.pattern_area_plateaus[<prior area>]` incremented (Iron Law #22
   auto-defeat uses the per-area counter sum).

## Required artifacts
- `runs/v(N+1)/brainstorm-v(N+1)-<chosen-area>.md` from Explorer using
  [templates/brainstorm-vN.md](../templates/brainstorm-vN.md).
- `audits/vN-pivot-decision.md` with:
  - Plateau evidence: last 3 versions' CV-mean ± std, Welch's t p-value.
  - `candidate_areas` ranking table.
  - Chosen area + justification (why this area vs. the alternatives).
  - Explorer's brainstorm summary.
  - Skeptic sign-off.
- `state.events_history` entry with `ref:
  audits/vN-pivot-decision.md`.

## Resolution criteria
`v(N+1)` enters FEATURE_MODEL AND `runs/v(N+1)/brainstorm-v(N+1)-<area>.md`
exists AND `coverage.json.pattern_areas[<chosen-area>]` has the pivot logged
in `notes_ref`.

## Anti-thrash guard
If the last 3 `auto-pivot` events have cycled through the same 2 areas,
orchestrator refuses the 4th pivot attempt and instead fires
`meta-audit-triggered` (premature cycling is trajectory-level drift, not a
per-version concern). Meta-Auditor evaluates whether the plateau signal
itself is miscalibrated (`plateau_threshold` too tight, Welch's t ignoring
seed-to-seed noise) and recommends either a threshold adjustment or
auto-defeat.

## Events this can chain into
- `auto-defeat` — if `candidate_areas` is empty.
- `meta-audit-triggered` — on anti-thrash guard activation.
- `coverage-stale` — if the new area's `last_tried_vN` was far in the past.

## Interactive-mode equivalent
Same evidence, same Explorer + Skeptic dispatches, but artefact is written
to `audits/vN-pivot-proposal.md` and orchestrator waits for user to confirm
or redirect. User's response logs an override-card if the user chooses a
different area than the top ranked.

## Resume phase
Orchestrator sets `state.current_v = N+1`, `state.current_phase = FEATURE_MODEL` (FRAME is bypassed — the pivot inherits the same data-contract and DGP as the plateaued line), and re-enters `playbooks/phase-feature-model.md` with the chosen-area brainstorm as pre-seed. `state.plateau_streak = 0`.
