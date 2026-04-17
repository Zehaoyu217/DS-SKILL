# Event: assumption-disproven

## Trigger
Statistician or Skeptic presents concrete falsification of an assumption declared in `data-contract.md` or `plans/vN.md` pre-registered decisions.

## Immediate response (in order)
1. Print banner to user naming the disproven assumption.
2. Write `disproven/vN-dNNN.md` documenting the falsification evidence (if using template, apply `templates/disproven-card.md`).
3. Update `data-contract.md` to remove or correct the assumption (git-tracked change).
4. Close current vN as incomplete; open v(N+1).
5. Prefill v(N+1) frame to start from the corrected assumption.

## Required artifacts
- Disproven card at `disproven/vN-dNNN.md` with evidence and persona sign-off.
- Updated `data-contract.md` with the corrected or removed assumption.
- `plans/v(N+1).md` that cites the disproven-card in its Trigger section and reflects corrected framing.

## Resolution criteria
Disproven card exists AND `data-contract.md` updated AND v(N+1) plan cites the disproven-card AND Skeptic re-signs the FRAME gate for v(N+1).

## Resume phase
Current vN is closed as incomplete. Orchestrator sets `state.current_v = N+1`, `state.current_phase = FRAME`, and re-enters `playbooks/phase-frame.md` starting from the corrected data-contract.
