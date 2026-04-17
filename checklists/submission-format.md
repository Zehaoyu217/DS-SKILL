# Checklist: Submission Format

For competition-mode external-submit only. Iron Law #16. Validates that the prediction file matches the organizer's `sample_submission.csv` exactly before the one-shot submission is sent.

## Required artifacts in `ds-workspace/`
- `data/sample_submission.csv` (or equivalent — name documented in `data-contract.md`)
- `submissions/vN/submission.csv` (or `.parquet` / `.json` matching organizer format)

## Checks (run by `scripts/check_submission_format.py`)

- [ ] **Row count** equals `sample_submission.csv` row count exactly.
- [ ] **ID column** name(s) match; set of IDs is identical (no extras, no missing).
- [ ] **ID order** matches sample-submission order unless organizer explicitly allows reordering.
- [ ] **Prediction column(s)** named exactly as in sample submission.
- [ ] **Dtypes** of prediction columns match (e.g., float vs int). Prediction column for probability tasks is float in `[0, 1]`.
- [ ] **Range / domain** of predictions is plausible: no NaN, no Inf, no negatives for non-negative targets, probabilities summing to 1 for multiclass softmax outputs.
- [ ] **File encoding and delimiter** match sample (UTF-8, comma, line ending, header presence).
- [ ] **Byte size** sanity: within 0.5× – 3× of `sample_submission.csv` unless organizer specifies otherwise.

## Submission hash discipline

- [ ] `sha256(submission.csv)` is computed and written to `submissions/vN/submission.sha256`.
- [ ] `submissions/vN/provenance.json` records: seed, env hash, data hash, winning-run id, timestamp, git commit.
- [ ] The exact same prediction file can be regenerated from the recorded seed/env/data/commit. Engineer verifies (full regen or sample-fold regen with byte-equal check on a fixed subset).

## Pre-submit declarations

- [ ] User has explicitly confirmed `ship external` or equivalent.
- [ ] Internal-ship already passed (internal holdout metric within predicted interval).
- [ ] Pre-registered decisions in `plans/v1.md` match actual final model choices, OR every divergence is listed with rationale in `audits/vN-ship-gate.md`.
- [ ] No pending CRITICAL findings from any persona.

## After submit

- [ ] State transitions to `submitted`. Orchestrator refuses further `/ds` modifications except `/ds reset-submission` (which the user must invoke explicitly, with rationale logged).
- [ ] Final report `report.md` generated and committed.

## Failure modes → events
- Any check failure fires `submission-drift` event.
- A retry requires remediation, re-sign of ship-gate by all four personas, and explicit user re-confirmation.
