# Iron Laws

Each law is enforced by a concrete mechanism. Rules without mechanisms are wishes.

## #1 Locked holdout exists before any modeling
**Mechanism:** `ds-workspace/holdout/HOLDOUT_LOCK.txt` contains sha256 + lock timestamp + "DO NOT READ UNTIL SHIP". Orchestrator maintains `state.holdout_reads` counter. VALIDATE phase refuses to read `holdout/` outside ship gate. Any unlogged read logged to `audits/vN-repro.md` and the run is marked `invalidated` on the dashboard.

## #2 CV scheme chosen before features
**Mechanism:** FRAME phase cannot exit until `audits/vN-cv-scheme.md` is signed by Validation Auditor. AUDIT/EDA/FEATURE_MODEL refuse to start without that signed file. Scheme decision uses [checklists/cv-scheme-decision.md](checklists/cv-scheme-decision.md).

## #3 No target-dependent fit on full data
**Mechanism:** Validation Auditor runs [checklists/leakage-audit.md](checklists/leakage-audit.md) — a grep playbook over `ds-workspace/src/` for known leak patterns (fit_transform before split, target encoding without CV, scaler fit on concat, `.fit(X_train)` outside pipeline). Hits fire the `leakage-found` event.

## #4 Every metric reported with uncertainty
**Mechanism:** Statistician rejects `runs/vN/metrics.json` lacking `cv_std` or `cv_ci95`. VALIDATE cannot sign off until uncertainty is present. Single-seed point estimates are rejected.

## #5 Baseline before complexity
**Mechanism:** FEATURE_MODEL entry checks `runs/*/metrics.json` for an entry tagged `baseline: true`. Absent → refuses non-baseline fits. Every later model reports `lift_vs_baseline` (not absolute score) on the leaderboard.

## #6 Disproven hypotheses are artifacts
**Mechanism:** FINDINGS exit requires every hypothesis id from `plans/vN.md` to resolve to a `findings/vN-fNNN.md` OR `disproven/vN-dNNN.md`. Orchestrator lists unresolved hypotheses and refuses exit.

## #7 Literature review before novel modeling
**Mechanism:** `novel-modeling-flag` fires when the proposed model family is outside `{linear, tree, gbm}`. Flag requires `literature/vN-memo.md` present before FEATURE_MODEL entry. Memo produced via [personas/literature-scout.md](personas/literature-scout.md).

## #8 Assumption tests before parametric stats
**Mechanism:** Statistician's [checklists/assumption-tests.md](checklists/assumption-tests.md) gates any parametric inference in findings. Failed assumptions block the inference (require non-parametric alternative or remediation).

## #9 Reproducibility: seed, env, data hash
**Mechanism:** Engineer checks that every `runs/vN/` contains `seed.txt`, `env.lock`, `data.sha256`. Re-runs one random CV fold from the seed/env; compares metrics within numerical tolerance. Mismatch = Engineer block. Details: [checklists/reproducibility.md](checklists/reproducibility.md).

## #10 Notebooks call `src/` only
**Mechanism:** Validation Auditor greps `nb/*.ipynb` cell sources for `class `, `def fit`, `sklearn.*\.fit(`, etc. Definitions in notebook cells are violations that block FINDINGS.

## #11 Every modeled run appears on the dashboard
**Mechanism:** FEATURE_MODEL and VALIDATE exits refuse if the run is not present in `ds-workspace/dashboard/data/leaderboard.json`. Writer contract in [dashboard-spec.md](dashboard-spec.md) is mandatory, not advisory.

---

## Enforcement pattern (common to all rules)

Phase transitions happen only when required files exist and have been signed. Persona output IS the signature. A gate is a checklist file; a sign-off is the filesystem-visible write of that checklist with the persona name filled in. This is mechanical, not advisory.
