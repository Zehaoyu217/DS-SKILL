# Event: covariate-shift

## Trigger
`checklists/adversarial-validation.md` reports `adv_auc > 0.60` OR `dup_ratio > 0.20`. Also fires manually if Explorer or Domain Expert detects segment-level drift during EDA.

## Immediate response (in order)
1. Print banner: `IRON LAW #13 — covariate shift detected (adv_auc=<x>, dup_ratio=<y>).`
2. Freeze current FEATURE_MODEL progress; existing runs remain on dashboard but are tagged `shift_pending: true`.
3. Branch on severity:
   - `0.60 ≤ adv_auc < 0.75` **or** `dup_ratio > 0.20` → **CV-scheme fix path.**
     Reopen CV scheme decision: dispatch Validation Auditor with the top drift
     features and require `audits/vN-cv-scheme.md` to be re-signed with a scheme
     appropriate to the drift (time split, group split, stratify-on-drift, or
     adversarial weighting). Current vN continues after the re-sign; existing
     runs are re-scored under the new scheme or marked `invalidated: suspected`
     if the re-score is infeasible.
   - `adv_auc ≥ 0.75` → **population-mismatch path.** BLOCK. This is not a
     CV-scheme fix — the training population does not cover the test population.
     Close current vN as `assumption-disproven` and open v(N+1) with a FRAME
     hypothesis that names the missing population coverage.

## Required artifacts
- `audits/vN-adversarial.md` (input; already produced by adversarial-validation checklist).
- `audits/vN-cv-scheme.md` re-signed with revised scheme and rationale that names the drift features.
- If the scheme chosen is stratify-on-drift or adversarial weighting, `src/cv/` contains the implementation and the leakage-audit and encoding-audit grep sweeps re-run clean.

## Resolution criteria
New CV scheme signed AND one re-baseline run completed under the new scheme AND adv-validation rerun after any feature drops: `adv_auc < 0.60` OR drift explicitly absorbed by the CV scheme.

## Resume phase
- **CV-scheme fix path** → resume at current vN `DGP` exit (re-sign
  `cv-scheme.md`) then re-enter `AUDIT` so adv-validation can re-run; rejoin
  `FEATURE_MODEL` only after AUDIT clears.
- **Population-mismatch path** → close current vN, open v(N+1) at `FRAME`.
  Do not attempt to resume modeling in the closed version.

## Don't
- Don't just remove the top drift feature if it is mechanistically important. Transform it (rank, bin, quantile-map) instead and re-check.
- Don't set aside the adv-AUC as "we'll worry about it later." The gap formula consumes it (Iron Law #13); late resolution invalidates the predicted interval at ship.
