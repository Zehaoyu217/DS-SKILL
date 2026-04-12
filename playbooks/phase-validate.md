# Phase: VALIDATE

## Entry gate
FEATURE_MODEL exited (run on dashboard, no active leakage patterns).

## Purpose
Statistical validation of the modeled run. Verify that metrics are reported with proper uncertainty, that underlying assumptions hold, and that CV-holdout gap can be predicted. This phase gates entry into FINDINGS.

## Steps (in order)
1. Statistician verifies that `runs/vN/metrics.json` contains `cv_std` and/or `cv_ci95` (Iron Law #4). Reject run if absent.
2. Statistician runs [checklists/assumption-tests.md](../checklists/assumption-tests.md) on the model residuals (normality, homoscedasticity, independence where applicable).
3. Validation Auditor re-confirms no new leakage via [checklists/leakage-audit.md](../checklists/leakage-audit.md) on final code state.
4. Statistician computes predicted CV-holdout gap from CV uncertainty (e.g., gap threshold for the `cv-holdout-drift` event at ship).
5. Document results in `audits/vN-assumptions.md` and `audits/vN-ship-gate.md` (draft threshold).

## Persona invocations
- **Statistician** (primary): Verify uncertainty presence, run assumption tests, compute gap threshold. Output: `audits/vN-assumptions.md` with Verdict [PASS | BLOCK].
- **Validation Auditor** (parallel, final leakage sweep): Output updated `audits/vN-leakage.md`.

## Exit gate
Statistician Verdict=PASS in `audits/vN-assumptions.md` AND uncertainty metrics present AND CV-holdout gap threshold recorded.

## Events that can abort this phase
- `leakage-found` (re-grep catches a new pattern; mark run invalidated and open v(N+1))
- `assumption-disproven` (assumption test fails critically; update data-contract and open v(N+1))
