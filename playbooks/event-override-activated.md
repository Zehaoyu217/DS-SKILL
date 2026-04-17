# Event: override-activated

## Trigger
A new `overrides/vN-override-<law-slug>.md` is created AND its id is added
to `state.active_overrides`. Emitted by the orchestrator at the moment of
write, not retrospectively at phase exit.

The event is a *log* — an audit trail entry — not a blocker. It ensures
every override is surfaced in `state.events_history` for dashboard rendering
and trajectory review by the Meta-Auditor.

## Immediate response (in order)
1. Append the event to `state.events_history` with `ref:
   overrides/<override-id>.md`.
2. Update `state.active_overrides` to include the new id.
3. Render in the dashboard Consistency panel with the override's scope and
   `expires_at`. Badge permanent-scope overrides separately (they require
   ship re-authorisation).
4. If `law ∈ {#1, #12, #16, #17, #20, budget}`, verify `signed_by`
   contains `user` regardless of scope. If not, fire
   `council-quorum-failed` with a structured error — these laws cannot
   be authorised by Council alone at any scope. Additionally, if
   `scope=permanent` AND `law ∈ {#16, #20}`, refuse the write — the
   linter rejects permanent scope for those laws outright.
5. If `scope=permanent` AND this is the third active permanent override
   (across all laws), fire `meta-audit-triggered` to catch scope creep.

## Lint coupling
`consistency_lint.py check_overrides()` enforces:
- `signed_by` is a YAML list (not a scalar).
- Permanent scope requires ≥2 signers.
- Any override of core laws (#1, #12, #16, #17, #20) or `law=budget`
  requires a `user` entry in `signed_by`, regardless of scope. Permanent
  scope on #16 or #20 is rejected outright (scope=run with a re-lock plan
  is the only path).
- `expires_at` is null only when `scope=permanent`.
- Every override-card file on disk has a matching `state.active_overrides`
  entry while its `expires_at` is in the future (reverse-sync check).
- Every `state.active_overrides` id has a matching file on disk (forward-
  sync check).
- Permanent overrides appearing at ship-gate have a re-authorisation
  section in `audits/vN-ship-gate.md`.

Any violation fails the gate that called the linter (FINDINGS, MERGE,
SHIP).

## Expiration lifecycle
- `scope=run`: orchestrator clears from `state.active_overrides` at the
  offending run's VALIDATE exit.
- `scope=version`: cleared at MERGE or SHIP exit for that version,
  whichever fires first.
- `scope=permanent`: never auto-cleared. Re-authorised at every SHIP gate.
  Can only be rescinded via explicit user `rescind-override <id>` command,
  which writes a paired `overrides/vN-override-rescind-<id>.md` note.

## Required artifacts
- `overrides/vN-override-<law-slug>.md` using
  [templates/override-card.md](../templates/override-card.md) — the
  override itself.
- `state.events_history` entry — the log.
- `state.active_overrides` update — the active-list.
- `audits/vN-ship-gate.md` §"Active overrides" re-authorisation (scope=
  permanent only) — at ship.

## Resolution criteria
Override expires naturally at scope-end OR is explicitly rescinded. The
`override-activated` event stays in `events_history` permanently as the
historical record; it is not removed when the override expires. Instead,
a paired audit entry in the step-journal notes the expiration.

## Events this can chain into
- `meta-audit-triggered` — on the third permanent override across all
  laws, or when the same law accumulates three run-scope overrides within
  5 versions.
- `council-quorum-failed` — when a core-law permanent override lacks a
  `user` signature.

## Dashboard
Overrides panel lists:
- All active overrides, badge-colored by scope (run=yellow,
  version=orange, permanent=red).
- Expired overrides (last 10) in a muted-grey history strip.
- Per-law counter: how many overrides this law has received across the
  project. Values ≥3 highlight systematic erosion.

## Resume phase
This event is a *log entry*, not a gate. After write + linter PASS, orchestrator resumes at `state.current_phase` (unchanged) with the new override visible in `state.active_overrides`. The override travels with the orchestrator until its scope-end (run VALIDATE exit, version MERGE/SHIP exit, or permanent re-auth at next SHIP).
