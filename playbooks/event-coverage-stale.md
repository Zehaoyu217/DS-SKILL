# Event: coverage-stale

## Trigger
For any `coverage.json.pattern_areas[<area>]` with `exhausted == false`:
`state.current_v - <area>.last_tried_vN >= 5`. The area has been neglected
for 5+ versions without being marked exhausted — either it was silently
skipped by the orchestrator's pivot priority, or its remaining_leverage
estimate is miscalibrated.

Emitted at VALIDATE exit when orchestrator updates `coverage.json`.

## Immediate response (in order)
1. Append `coverage-stale` to `state.events_history` with `ref:
   coverage.json#<area-id>`.
2. Do NOT immediately force exploration of the stale area — some areas
   are legitimately low-leverage and not visited by design. Instead,
   schedule the area for re-evaluation at the next auto-pivot decision.
3. Update the `candidate_areas` ranking in
   [event-auto-pivot.md](event-auto-pivot.md) step 2: stale areas get a
   +0.1 priority bump (so they are preferred when tied with fresh low-
   leverage candidates). Capped at one bump per area per vN so stale
   areas don't dominate.

## Dashboard surfacing
Coverage panel highlights stale areas with a ⚠ badge and the number of
versions since `last_tried_vN`. Stale-for-10+ versions warrants user
attention even in autonomous mode — fires
`escalate_to_human.meta_auditor_critical_finding` if the area is not
picked up by the next pivot.

## Remediation paths

### Path A — Stale-but-low-leverage (the common case)
- Re-evaluate `remaining_leverage_estimate` in `coverage.json` based on
  current leaderboard trajectory.
- If `remaining_leverage_estimate < 0.1`, mark `exhausted = true` with
  `ceiling_reason: low-leverage`. This documents the choice rather than
  silently skipping.
- Write a one-line rationale in `coverage.json.pattern_areas[<area>]
  .notes_ref` pointing to the leaderboard run that supports the
  low-leverage assessment.

### Path B — Stale-and-worth-exploring
- Orchestrator forces the area into the next `auto-pivot` candidate list
  regardless of priority order.
- Dispatches Explorer with the stale area as focus.
- On the exploration's VALIDATE exit, `remaining_leverage_estimate` is
  updated to reflect the new evidence.

### Path C — Systematic-coverage-gap
- If three areas fire `coverage-stale` in the same vN, the loop's
  exploration strategy is biased. Fire `meta-audit-triggered` to review
  the `pivot_priority_order` for miscalibration.

## Required artifacts
- Updated `coverage.json` with either a new `remaining_leverage_estimate`
  (path A/B) or an `exhausted` flag (path A terminal).
- `step-journal/vN.md` entry linking to the event.

## Resolution criteria
Either:
- `coverage.json.pattern_areas[<area>].exhausted == true` with a
  `ceiling_reason` (path A), OR
- `<area>.last_tried_vN` has advanced past the stale threshold because a
  run visited the area (path B), OR
- Meta-Auditor has reviewed and re-authorised the current
  `pivot_priority_order` (path C).

## Events this can chain into
- `auto-pivot` — when path B forces a pivot to the stale area.
- `meta-audit-triggered` — on path C systematic gap.

## Interactive mode
Same event emission, but the orchestrator surfaces the stale area to the
user as an advisory rather than auto-bumping priority. User can
explicitly direct exploration of the area via `/ds explore <area>`.

## Resume phase
- **Path A (mark exhausted):** `coverage.json` updated in place. Orchestrator resumes at `state.current_phase` — typically proceeds into the next phase or next vN as if the event had not fired.
- **Path B (force pivot):** chains into `auto-pivot`; resume logic follows that event (opens v(N+1) at FEATURE_MODEL with Explorer brainstorm pre-seeded).
- **Path C (meta-audit):** chains into `meta-audit-triggered`; resume logic follows that event (gate held until Meta-Auditor PASS).
