# Event: submission-drift

## Trigger
Any of:
- `scripts/check_submission_format.py` exits non-zero.
- Row count / ID set / column schema of `submissions/vN/submission.csv` differs from `data/sample_submission.csv`.
- Prediction column contains NaN, Inf, out-of-domain values, or dtype mismatch.
- `sha256` regeneration does not reproduce the existing submission byte-for-byte (non-determinism in inference path).

## Immediate response (in order)
1. Print banner: `IRON LAW #16 — submission-drift detected. External-submit BLOCKED.`
2. Do not send anything. The one-shot external-submit is still intact.
3. Snapshot the failing submission as `submissions/vN/submission.rejected.<timestamp>.csv` for post-mortem.
4. Dispatch Engineer to remediate:
   - If format error: fix inference script, regenerate, re-run `check_submission_format.py`.
   - If non-determinism: find the non-deterministic step (thread order, GPU non-determinism, Python hash randomization), fix seed handling, regenerate.
5. Full ship-gate must be re-signed after remediation (all five personas). User must re-confirm `ship external`.

## Required artifacts
- `audits/vN-submission-drift.md`: failure mode, remediation, regeneration sha256, re-sign log.
- Updated `submissions/vN/provenance.json` with the new sha256 and any code changes applied.

## Resolution criteria
`scripts/check_submission_format.py` exits 0 AND regeneration from recorded seed/env/data produces byte-equal output on a spot-sampled subset AND ship-gate re-signed.

## Don't
- Don't submit "close enough" when a column dtype is wrong. The organizer's grader will reject or silently misinterpret.
- Don't generate a new submission from a hotfix without re-running the full ship-gate. Fast submissions are how one-shot competitions are lost.

## Resume phase
Orchestrator re-enters SHIP Stage 1 (`checklists/ship-gate.md`) — all five personas re-sign, and the Skeptic + Statistician debate is re-run. Only after Stage 1 fully re-signs may Stage 2 (external-submit) be re-opened with a fresh user `ship external` confirmation.
