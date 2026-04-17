# Event: auto-defeat

## Trigger
Either condition fires:
1. All `coverage.json.pattern_areas[]` have `exhausted == true` with
   `ceiling_reason ∈ {approach-exhausted, feature-limited, intrinsic}`,
   OR
2. `sum(state.pattern_area_plateaus.values()) >=
   autonomous.yaml.autonomy.exhaustion_threshold` (default 6) — total
   plateaus across all areas.

Fires only when `state.autonomous == true`. Interactive mode writes an
advisory `audits/vN-surrender-proposal.md` and waits for user.

## Immediate response (in order)
1. **Freeze all runs.** No new runs, no phase transitions, until the auto-
   defeat ceremony completes.
2. Dispatch **Meta-Auditor** per
   [personas/meta-auditor.md](../personas/meta-auditor.md). This is a
   trajectory review — was the loop actually exhausted, or did we prematurely
   declare ceilings?
3. Await Meta-Auditor verdict:
   - **PASS** → proceed to §Surrender ceremony.
   - **BLOCK** → proceed to §Meta-Auditor block.

## Surrender ceremony (Meta-Auditor PASS)
1. Write `disproven/surrender-v<current_v>.md` using
   [templates/surrender-card.md](../templates/surrender-card.md) with:
   - `reason ∈ {exhaustion, budget-capped, intrinsic-ceiling,
     assumption-falsified}` — pick the dominant one.
   - Ceiling evidence from `coverage.json`: per-area `approaches_tried` +
     `ceiling_reason`.
   - Budget evidence from `budget.json`: spend vs. envelope.
   - Leaderboard trajectory: last 5 versions' best CV-mean + trend.
   - Meta-Auditor verdict + reference to `audits/meta/vN-meta-audit.md`.
2. Write `audits/vN-final-report.md` summarising: what was tried, what was
   ruled out, what is still unknown. This is the lessons payload for
   future projects on similar problems.
3. Append `auto-defeat` to `state.events_history` with `ref:
   disproven/surrender-v<current_v>.md`.
4. Set `state.phase = ABORTED`.
5. Emit the final report to user; stop.

No further autonomous runs until user issues explicit `reset-surrender`
command. `reset-surrender` requires the user to re-author `plans/v(N+1).md`
with a revised hypothesis that addresses the surrender card's documented
ceilings.

## Meta-Auditor block
If Meta-Auditor returns BLOCK (trajectory review finds the exhaustion
signal unreliable):
1. Do NOT emit a surrender card.
2. Apply Meta-Auditor's recommendation:
   - **Re-tune thresholds** — adjust `plateau_threshold` or
     `exhaustion_threshold` in `autonomous.yaml`; this is itself an Iron
     Law #24 override (scope=permanent, `law=autonomy-thresholds`) that
     requires user sign-off because it modifies the autonomous-mode contract.
   - **Re-seed coverage** — if the block diagnoses premature ceiling
     declarations, mark specific `coverage.json` entries as
     `exhausted = false` with rationale.
   - **Escalate** — fire
     `escalate_to_human.meta_auditor_critical_finding`; autonomous mode
     exits, interactive mode resumes.
3. Regardless of chosen recovery, write
   `audits/vN-defeat-blocked.md` documenting the Meta-Auditor findings.

## Required artifacts (surrender path)
- `disproven/surrender-v<current_v>.md`
- `audits/meta/vN-meta-audit.md`
- `audits/vN-final-report.md`
- `state.phase = ABORTED`

## Required artifacts (block path)
- `audits/vN-defeat-blocked.md`
- Optional: updated `autonomous.yaml` (if thresholds re-tuned) with
  corresponding override-card.
- `state.phase` unchanged.

## Resolution criteria
Surrender path: `state.phase == ABORTED` AND surrender card + final report
exist AND `consistency_lint.py` exits 0 (no dangling hypotheses).

Block path: `audits/vN-defeat-blocked.md` exists AND the chosen recovery
action is logged (threshold override OR coverage re-seed OR escalation),
and loop has either resumed with new parameters or exited to interactive.

## Events this can chain into
- `meta-audit-triggered` — always, as step 2 of the ceremony.
- `override-activated` — when threshold re-tuning writes a new override.
- Escalation (non-event): `escalate_to_human.meta_auditor_critical_finding`
  or `escalate_to_human.surrender_card_emitted`.

## Anti-gaming
Consistency linter refuses SHIP at a later date (if user revives the
project) without explicit acknowledgement of the surrender card.
`disproven/surrender-vN.md` is the filesystem proof that a bounded
autonomous loop terminated legitimately.

## Resume phase
- **Surrender path:** terminal. `state.phase = ABORTED`. No phase entry. Resume requires explicit user `reset-surrender` + re-authored `plans/v(N+1).md` addressing the surrender card's ceilings.
- **Block path (threshold re-tune):** `state.phase` unchanged; resume at `state.current_phase` with the new thresholds active.
- **Block path (coverage re-seed):** resume at `state.current_phase`; the next pivot decision uses the re-seeded coverage.
- **Block path (escalate):** `state.autonomous = false`; next `/ds` invocation resumes in interactive mode at `state.current_phase`.
