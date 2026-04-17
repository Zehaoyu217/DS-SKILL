# Event: suspicious-lift

## Trigger
Any of:
- Single-fold CV jumps >3σ above the baseline mean for the corresponding fold.
- Seed-to-seed std on a top-model candidate exceeds 50% of `lift_vs_baseline`.
- CV metric exceeds the strongest prior-art number in `literature/vN-memo.md` by more than the memo's reported variance, with no named mechanism.
- Narrative audit flags "I can't explain why this works" on a top-3 candidate.

## Immediate response (in order)
1. Print banner: `SUSPICIOUS LIFT — freezing run <id> as invalidated: suspected until audited.`
2. Mark the run `invalidated: suspected` on the dashboard (not `invalidated: true` yet). Suspect runs render with a muted style; leaderboard re-ranks without them but does not drop them from history.
3. Dispatch Skeptic and Validation Auditor in parallel:
   - Skeptic reviews `findings/` and plan for post-hoc drift and missing controls.
   - Validation Auditor re-runs full leakage-audit + encoding-audit on the offending run's code path.
4. If either audit finds a concrete cause: fire the appropriate event (`leakage-found`, `assumption-disproven`), write the disproven/finding card, proceed.
5. If neither audit finds a cause: require **independent replication** — either a different seed set (≥5 seeds) or a different CV fold assignment. If replication reproduces the lift with the same magnitude, the run is cleared and the narrative audit must still pass before SHIP.

## Required artifacts
- `audits/vN-suspicious-<runid>.md`: timeline of suspicion trigger, audit steps taken, replication results, final verdict.
- Finding or disproven card as appropriate.

## Resolution criteria
Either:
- Cause identified → run marked `invalidated: true`, remediation hypothesis opened in v(N+1), OR
- Replication clean + narrative signed → run marked `valid` again, SHIP may proceed.

## Resume phase
- **Cause identified** → close current vN and resume at v(N+1) `FRAME` (fresh
  framing for the remediation hypothesis) OR v(N+1) `AUDIT` if the cause is
  a leak/encoding fix scoped tightly enough that framing is unchanged. The
  disproven-card (or leakage event) names which.
- **Replication clean** → resume at the phase that fired the event (usually
  `FEATURE_MODEL` step 9 or `VALIDATE`); un-freeze the run and continue the
  exit-gate sequence.

## Don't
- Don't ship a suspicious run without Narrative Audit PASS on the independent replication.
- Don't dismiss the trigger as "we got lucky." Every 3σ jump has a cause — either a real signal or a leak. Name it.
