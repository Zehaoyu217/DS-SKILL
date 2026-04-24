# Phase: VALIDATE

## Entry gate
FEATURE_MODEL exited (run on dashboard, no active leakage patterns, ablation log present, AND `audits/vN-model-diagnostics.md` present — Iron Law #18 requires diagnostics before validation).

**Eval harness lock check (Iron Law #20):** Run before any validation steps:
```
python $SKILL/scripts/hash_eval_harness.py <ds-workspace> --check
```
Exit 1 fires the `eval-harness-tampered` event and blocks this phase until the override is recorded.

## Purpose
Statistical validation of the modeled run. Verify that metrics are reported with proper uncertainty and multi-seed stability, that underlying assumptions hold, and that the **expanded** CV-holdout gap can be predicted (CV std + adversarial drift + duplicate ratio, Iron Law #13). This phase gates entry into FINDINGS.

## Steps (in order)
1. Statistician verifies `runs/vN/metrics.json` contains `cv_std` AND `cv_ci95` AND `seeds` list AND `seed_std` (Iron Law #4). Reject run if any absent.
2. Statistician runs [checklists/assumption-tests.md](../checklists/assumption-tests.md) on the model residuals (normality, homoscedasticity, independence where applicable).
3. Multi-seed stability: if `seed_std > 0.5 · lift_vs_baseline`, fire `suspicious-lift` event and freeze the run.
4. Validation Auditor re-confirms no new leakage via [checklists/leakage-audit.md](../checklists/leakage-audit.md) + [checklists/encoding-audit.md](../checklists/encoding-audit.md) on final code state.
5. **Expanded predicted interval.** Compute:
   `predicted_interval = cv_mean ± (2·cv_std + λ·max(0, adv_auc - 0.5) + μ·dup_ratio)`
   with `adv_auc` and `dup_ratio` from `audits/vN-adversarial.md` and defaults `λ = 0.2`, `μ = 0.3` (or problem-specific values documented in `plans/vN.md`). Record in `audits/vN-ship-gate.md` (draft threshold).
6. Document residual assumption-test results in `audits/vN-assumptions.md`.
7. **Close plan-updates log.** Append the final revision + "Summary at close" block to `plans/v{N}-updates.md` per [templates/plan-updates-vN.md](../templates/plan-updates-vN.md). Set `status: closed` in the frontmatter. This paragraph is the primary input for the next iteration's FRAME phase.

7a. **Git-commit the final validated run artifacts:**
    ```
    bash $SKILL/scripts/log_run_commit.sh ds-workspace runs/vN <run-id> "VALIDATE: final run, uncertainty verified"
    ```
    Commit sha is recorded in `audits/vN-repro.md` for reproducibility cross-reference (Engineer step). Skip if project is not a git repo.

8. **Model-as-Teacher synthesis** (Iron Law #26). The orchestrator writes `audits/vN-model-synthesis.md` using [templates/model-synthesis.md](../templates/model-synthesis.md) and verifies every box in [checklists/model-as-teacher.md](../checklists/model-as-teacher.md). The synthesis reads `audits/vN-model-diagnostics.md`, `runs/vN/metrics.json`, and `knowledge-base.md`, and distills *deltas, shape-changes, and implications* — it does not duplicate the raw diagnostics. Empty §6 (Implications) or generic §6 bullets fail the gate in competition mode (warn in daily). Skeptic micro-review is required in competition mode when §6 updates a DGP hypothesis. After synthesis exits the gate, the orchestrator applies any §7 proposed KB patches via `/ds-kb apply-patches audits/vN-model-synthesis.md` and updates `coverage.json.pattern_areas[].approaches_tried` + `remaining_leverage_estimate` in line with the synthesis's implications.

## Persona invocations
- **Statistician** (primary): Verify uncertainty presence, run assumption tests, run multi-seed stability check, compute expanded gap threshold. Output: `audits/vN-assumptions.md` with Verdict [PASS | BLOCK] and gap interval logged in `audits/vN-ship-gate.md`.
- **Validation Auditor** (parallel, final leakage + encoding sweep): Output updated `audits/vN-leakage.md` and `audits/vN-encoding.md`.

## Exit gate
All of the following must hold (ALL AND):
- Statistician Verdict=PASS in `audits/vN-assumptions.md`
- Uncertainty and seed-stability metrics present in `runs/vN/metrics.json`
- Expanded predicted interval recorded in `audits/vN-ship-gate.md`
- `plans/v{N}-updates.md` has `status: closed` and a "Summary at close" block
- `runs/v{N}/learnings.md` has a VALIDATE exit entry appended
- `runs/v{N}/learnings.md` frontmatter `status: closed` and "Summary at close" block written (primary input for DGP §6 in v(N+1))
- `audits/vN-model-synthesis.md` exists and passes `checklists/model-as-teacher.md` (Iron Law #26 — blocking in competition mode, warning in daily mode)
- Proposed KB patches from the synthesis's §7 have been applied (or explicitly deferred with reason) and `coverage.json` updated to reflect the version's approaches and leverage estimates

## Events that can abort this phase
- `leakage-found` (re-grep catches a new pattern; mark run invalidated and open v(N+1))
- `assumption-disproven` (assumption test fails critically; update data-contract and open v(N+1))
- `suspicious-lift` (seed instability exceeds threshold)
