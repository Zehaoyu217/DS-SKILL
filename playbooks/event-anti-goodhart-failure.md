# Event: anti-goodhart-failure

## Trigger
At VALIDATE exit, a run's primary metric has improved over the previous
version's best but at least one pre-registered `secondary_metrics` entry has
degraded >Nσ below the feature-baseline value for that metric, where N =
`autonomous.yaml.secondary_metrics[].max_degradation_sigma` (default 2.0).

The checker is `checklists/anti-goodhart.md` — run by the Statistician at
VALIDATE exit. Emits `anti-goodhart-failure` to `state.events_history` with
`ref` pointing to the offending `runs/vN/<run_id>/metrics.json`.

## Immediate response (in order)
1. **Block the run from ship promotion.** The run remains in
   `leaderboard.json` but is marked `ship_candidate: false` until resolved.
2. Dispatch **Statistician** to verify the degradation is not a
   seed-variance artifact — re-run with ≥3 seeds if the original was
   single-seed.
3. Dispatch **Skeptic-variant-C** (Goodhart-prior) to evaluate whether the
   primary improvement is genuinely useful given the secondary degradation.
   Example questions:
   - Does the degraded secondary represent a real-world cost (calibration
     for downstream probabilistic decisions, worst-segment score for
     fairness, etc.)?
   - Is the primary improvement concentrated in exactly the segments where
     the secondary degraded? (Goodhart fingerprint: primary lift from
     easy rows while hard rows regress.)
4. Dispatch **Domain Expert** if available (or Literature Scout + Meta-
   Auditor in autonomous mode) to judge whether the trade-off is
   acceptable for the declared `decision_supported`.

## Remediation paths

### Path A — Reject the run
- Mark `leaderboard.json[run_id].status = "rejected-goodhart"` with
  `rejection_reason: "secondary <metric> degraded <X>σ"`.
- No override-card needed (rejection is the default path and the artifact
  is the status field).
- Emit a `disproven/vN-dNNN.md` card if the approach family is now ruled
  out (e.g., "calibration shrinkage does not compose with this
  loss function").
- Continue FEATURE_MODEL with a non-Goodhart candidate from the existing
  brainstorm OR dispatch Explorer for a fresh brainstorm targeting the
  degraded secondary.

### Path B — Accept with override (the trade-off is legitimate)
- Author `overrides/vN-override-anti-goodhart-<metric>.md` using
  [templates/override-card.md](../templates/override-card.md) with:
  - `law: anti-goodhart-<metric>` (e.g., `anti-goodhart-calibration_ece`)
  - `scope: run` (single-run exception; version-scope requires Council +
    Meta-Auditor and is rarely appropriate)
  - `expected_risk`: exact σ of degradation on the secondary; downstream
    impact description.
  - `mitigation`: compensating action (e.g., "post-hoc Platt scaling
    applied at inference to recover calibration").
  - `signed_by`: `[user]` in interactive mode; `[council]` in autonomous
    mode (Council-only for run-scope is permitted).
  - `affected_runs: [<run_id>]`
- Update `leaderboard.json[run_id].status = "accepted-with-goodhart-
  override"` and `override_refs: [override-id]`.
- At SHIP gate, `checklists/ship-gate.md` §"Anti-Goodhart re-
  authorisation" re-lists every `anti-goodhart-*` override for explicit
  approval; unresolved ones refuse ship.

### Path C — Expand the secondary-metrics list
- The degradation reveals a blind spot in the pre-registered secondary-
  metrics list. Iron Law #23 permits adding new secondaries mid-project;
  removal requires override.
- Author an amendment to `plans/vN.md` §pre_registration.secondary_metrics
  with the new metric included; log the amendment in
  `plans/vN-updates.md`.
- Existing runs are back-scored on the new secondary and leaderboard
  re-rendered. Runs that now fail the new secondary become
  `anti-goodhart-failure` events retroactively.

## Narrative audit coupling (Iron Law #14)
At SHIP, `checklists/narrative-audit.md` §"Goodhart risk" explicitly
requires every top feature that improves primary but worsens a secondary
to be acknowledged. Any top-K feature with Goodhart fingerprint without
acknowledgement blocks ship regardless of active overrides.

## Required artifacts
- Path A: `leaderboard.json` status update + optional `disproven/vN-dNNN.md`.
- Path B: `overrides/vN-override-anti-goodhart-<metric>.md` +
  leaderboard status update + `state.active_overrides` entry.
- Path C: `plans/vN-updates.md` entry + re-scored leaderboard.
- All paths: step-journal entry linking to the event.

## Resolution criteria
Either:
- Offending run is rejected (path A) OR replaced by a non-Goodhart
  candidate for ship selection, OR
- A valid override exists AND Council (or user) has signed AND Iron Law
  #14 narrative audit acknowledges the Goodhart trade-off (path B), OR
- Secondaries list has been amended and all runs re-scored (path C).

## Events this can chain into
- `override-activated` — when path B's override is filed.
- `meta-audit-triggered` — if three path-B overrides are filed for the
  same secondary within 5 versions (systematic erosion is a trajectory
  concern, not per-version).

## Resume phase
- **Path A (reject):** resume at FEATURE_MODEL (current phase or re-entry) with a non-Goodhart candidate from brainstorm.
- **Path B (accept-with-override):** resume at VALIDATE exit — proceed to FINDINGS carrying the override in `state.active_overrides`. Re-authorised at SHIP gate.
- **Path C (amend secondaries):** re-score all runs on the new metric, re-render leaderboard, then resume at the phase where the event fired. Any run newly failing becomes a fresh `anti-goodhart-failure` event.
