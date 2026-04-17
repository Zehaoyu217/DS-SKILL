# Iron Laws

Each law is enforced by a concrete mechanism. Rules without mechanisms are wishes.

## #1 Locked holdout exists before any modeling
**Mechanism:** `ds-workspace/holdout/HOLDOUT_LOCK.txt` contains sha256 + lock timestamp + "DO NOT READ UNTIL SHIP". Orchestrator maintains `state.holdout_reads` counter. VALIDATE phase refuses to read `holdout/` outside ship gate. Any unlogged read logged to `audits/vN-repro.md` and the run is marked `invalidated` on the dashboard. In a one-shot external competition, the *internal* holdout may be read once at internal-ship; the organizer's *hidden test* is submitted to exactly once at external-submit.

## #2 CV scheme chosen before features
**Mechanism:** FRAME phase cannot exit until `audits/vN-cv-scheme.md` is signed by Validation Auditor. AUDIT/EDA/FEATURE_MODEL refuse to start without that signed file. Scheme decision uses [checklists/cv-scheme-decision.md](checklists/cv-scheme-decision.md) and must be consistent with the shift axes declared in the DGP memo (Iron Law #12).

## #3 No target-dependent fit on full data
**Mechanism:** Validation Auditor runs [checklists/leakage-audit.md](checklists/leakage-audit.md) — a grep playbook over `ds-workspace/src/` for known leak patterns (fit_transform before split, target encoding without CV, scaler fit on concat, `.fit(X_train)` outside pipeline, stacking without OOF). Hits fire the `leakage-found` event. Extended with [checklists/encoding-audit.md](checklists/encoding-audit.md) for encoder-specific audits (Iron Law #13).

## #4 Every metric reported with uncertainty
**Mechanism:** Statistician rejects `runs/vN/metrics.json` lacking `cv_std` or `cv_ci95`. VALIDATE cannot sign off until uncertainty is present. Single-seed point estimates are rejected. Multi-seed stability required for any candidate promoted to ship (≥3 seeds; report seed-to-seed std separately from fold std).

## #5 Baseline before complexity
**Mechanism:** FEATURE_MODEL entry checks `runs/*/metrics.json` for an entry tagged `baseline: true`. Absent → refuses non-baseline fits. Every later model reports `lift_vs_baseline` (not absolute score) on the leaderboard.

## #6 Disproven hypotheses are artifacts
**Mechanism:** FINDINGS exit requires every hypothesis id from `plans/vN.md` to resolve to a `findings/vN-fNNN.md` OR `disproven/vN-dNNN.md`. Orchestrator lists unresolved hypotheses and refuses exit. Branches killed during MERGE (Iron Law #15) also emit disproven-cards.

## #7 Literature review before any plan
**Mechanism:** Lite-mode Literature Scout memo `literature/vN-memo.md` is required at FRAME exit, regardless of model novelty. Full-mode memo required when `novel-modeling-flag` (model outside `{linear, tree, gbm}`), `novel-feature-flag` (feature engineering approach outside `{raw, binned, log-transform, interaction, aggregation, categorical-encoding, embedding}`), or `metric-plateau` fires. Memo produced via [personas/literature-scout.md](personas/literature-scout.md). If both novel flags fire simultaneously, a single Full memo covering both is acceptable.

## #8 Assumption tests before parametric stats
**Mechanism:** Statistician's [checklists/assumption-tests.md](checklists/assumption-tests.md) gates any parametric inference in findings. Failed assumptions block the inference (require non-parametric alternative or remediation).

## #9 Reproducibility: seed, env, data hash
**Mechanism:** Engineer checks that every `runs/vN/` contains `seed.txt`, `env.lock`, `data.sha256`. Re-runs one random CV fold from the seed/env; compares metrics within numerical tolerance. Mismatch = Engineer block. Details: [checklists/reproducibility.md](checklists/reproducibility.md).

## #10 Notebooks call `src/` only
**Mechanism:** Validation Auditor greps `nb/*.ipynb` cell sources for `class `, `def fit`, `sklearn.*\.fit(`, etc. Definitions in notebook cells are violations that block FINDINGS.

## #11 Every modeled run appears on the dashboard
**Mechanism:** FEATURE_MODEL and VALIDATE exits refuse if the run is not present in `ds-workspace/dashboard/data/leaderboard.json`. Writer contract in [dashboard-spec.md](dashboard-spec.md) is mandatory, not advisory.

## #12 DGP memo signed before AUDIT
**Mechanism:** A new phase `DGP` sits between FRAME and AUDIT. Exit requires signed `dgp-memo.md` (template: [templates/dgp-memo.md](templates/dgp-memo.md)) with Skeptic + Validation Auditor + Domain Expert sign-offs (Domain Expert may be waived with written rationale). Any feature tagged `at-label` or `post-label` without explicit justification blocks. See [playbooks/phase-dgp.md](playbooks/phase-dgp.md).

## #13 Distribution shift is measured, not assumed
**Mechanism:** AUDIT phase runs [checklists/adversarial-validation.md](checklists/adversarial-validation.md): train a classifier to distinguish train vs. test rows, report AUC. AUC > 0.60 forces a matching CV scheme (time-based, group-based, or stratified-by-drift-feature). Duplicate and near-duplicate detection between train/test is also run here. Results feed the expanded gap formula in VALIDATE: `predicted_interval = cv_mean ± (2·cv_std + λ·max(0, adv_auc - 0.5) + μ·dup_ratio)`.

## #14 Model tells a story — narrative audit before ship
**Mechanism:** Before SHIP, [checklists/narrative-audit.md](checklists/narrative-audit.md) runs: top-K feature importances / SHAP directions are compared against the DGP memo §7 pre-registered expectations. Unexpected top features must be explained or disqualified. Counterfactual spot-checks on ≥3 rows required. Skeptic signs. Discrepancy without explanation blocks ship.

## #15 Parallel branches merge via disproven-cards
**Mechanism:** When multiple sub-plans `vN.a`, `vN.b`, `vN.c` run in parallel, the MERGE phase [playbooks/phase-merge.md](playbooks/phase-merge.md) keeps the winning branch's code path and emits a `disproven/` card for every feature/model dropped. No silent dropping. Winner chosen by CV with uncertainty, not by eyeballing.

## #16 One-shot submission discipline (competition mode only)
**Mechanism:** If the user has declared a one-shot external submission (competition mode), SHIP splits into **internal-ship** (reads locked internal holdout exactly once, validates predicted interval) and **external-submit** (generates prediction file, validates format against `sample_submission.csv` via [checklists/submission-format.md](checklists/submission-format.md), logs sha256 of submission, commits). External-submit is one-way: state moves to `submitted` and no further code changes are permitted without explicit `reset-submission` by the user. In daily mode, this law does not apply.

## #17 Knowledge is aligned, not accreted
**Mechanism:** FINDINGS exit, MERGE exit, and SHIP entry refuse to proceed unless `python scripts/consistency_lint.py ds-workspace` exits 0. The linter cross-references claim blocks across plan / DGP §7a predictions / findings / disproven / step-journal / lessons / leaderboard and fails on:
- unresolved hypotheses
- unknown DGP prediction refs
- opposite-direction live claims on the same subject
- broken `supersedes` chains
- orphan top-priority DGP predictions
- silent primary-metric drift across versions
- leaderboard top-run not claimed by any finding

Warnings render on the dashboard's Consistency panel — new claims are checked against *all* prior claims every phase, not accreted silently. **Daily mode:** blocking at SHIP only; warnings at FINDINGS/MERGE.

## #18 Model diagnostics before validation
**Mechanism:** After every candidate model in FEATURE_MODEL and before VALIDATE, the orchestrator runs [checklists/model-diagnostics.md](checklists/model-diagnostics.md). Required artifacts:
- SHAP values (global + local)
- Partial dependence plots (PDP) — compared against DGP §7a predictions
- Individual conditional expectation (ICE) plots
- Permutation importance
- Segment-level weakness analysis (continuous feature quantiles + categorical breakdowns)
- Residual analysis

Segments where validation metric drops >1σ below overall are flagged for feature engineering, confounding investigation, or documentation as known limitations. Output: `audits/vN-model-diagnostics.md` + plots in `runs/vN/plots/`. Applies in both modes — understanding the model is never optional.

## #19 Brainstorm-before-build and feature-baseline discipline
**Mechanism:** Two coupled requirements that force genuine exploration instead of picking the first reasonable approach. As of Iron Law #25, brainstorm triggers are **novelty-driven** via `coverage.json` — see #25. Phase-driven triggers remain the v1 default and the fallback when `coverage.json` is absent.

**(a) Brainstorm-before-build.** On v1 (or when `coverage.json` shows an unexplored pattern area), DATA_PREP, FEATURE_MODEL, and (if tuning) TUNING each require `runs/v{N}/brainstorm-v{N}-<PHASE>.md` using [templates/brainstorm-vN.md](templates/brainstorm-vN.md) with:
- ≥3 candidate approaches
- Rejected alternatives explained
- One named contingency

The FEATURE_MODEL brainstorm also needs a Skeptic micro-audit before step 0.1 exits. `consistency_lint` rejects vN reaching FEATURE_MODEL exit without the brainstorm files, *except* when `coverage.json` shows the approach family was previously brainstormed and the prior brainstorm is cited in `notes_ref`. An Explorer subagent is dispatched on first entry to any pattern area to seed the brainstorm with creative candidates *before* the orchestrator's preferred approach is fixed.

**(b) Feature baseline.** FEATURE_MODEL entry requires at least one `runs/*/metrics.json` tagged `feature_baseline: true` (raw features against model baseline). Later candidates report `feature_lift_vs_feature_baseline` separately from `lift_vs_baseline` so feature-engineering lift is distinguishable from model-family lift. If tuning: a default-params reference run is logged first; tuned runs report `tuning_lift_vs_default`. Absence of feature-baseline blocks FEATURE_MODEL entry. Identical in both modes — narrow exploration is the laziness failure mode this law prevents.

### Addendum: two-tier pre-screen (applies within #19a FEATURE_MODEL brainstorm)

Before step 0.2 (feature-engineering brainstorm), a cheap 1-fold pre-screen filters obvious losers from the model-family brainstorm (step 0.1). Results are recorded in `runs/v{N}/screen-results.json`. Candidates with `"passed": false` are recorded with rejection reason; they do not receive a full disproven-card (too lightweight), but their id is logged in the brainstorm's `rejected_alternative_ids`. The pre-screen does NOT apply to the DATA_PREP brainstorm. Threshold: `feature_baseline_cv_mean - 2 × feature_baseline_cv_std` (permissive by design; known calibration choice, revisable). For temporal CV schemes, the 1-fold screen uses the terminal fold.

## #20 Eval harness is locked after AUDIT
**Mechanism:** At AUDIT exit, `scripts/hash_eval_harness.py ds-workspace` (write mode) computes the sha256 of every `.py` in `src/evaluation/` (excluding `__pycache__`) and writes the hash to `data-contract.md` §Eval harness lock. At every later gate (FEATURE_MODEL/VALIDATE/SHIP entry), the Validation Auditor runs `--check` as part of [checklists/leakage-audit.md](checklists/leakage-audit.md). Mismatch fires `eval-harness-tampered` and refuses the phase. Overrides use Iron Law #24 (`law=eval-harness`, `scope=run|version`; **permanent scope rejected outright**). Each affected run is individually marked valid or invalidated — no bulk invalidation. Applies in both modes.

## #21 Budget envelope declared at FRAME
**Mechanism:** FRAME exit requires `ds-workspace/budget.json` (schema: [templates/budget.schema.json](templates/budget.schema.json)) declaring `{compute_hours, wall_clock_days, api_cost_usd, max_versions, max_runs_per_version}`. Every run calls `scripts/budget_check.py ds-workspace --account <run_id> --cost <hours,usd>` which decrements envelopes and writes `runs/vN/<run_id>/budget-ledger.json`. If any dimension reaches ≤0, `budget-exceeded` fires and further runs are refused until either:
- User authorizes an Iron Law #24 override (`law=budget`, `scope=run|version`; **permanent scope requires `user` in `signed_by`, never Council alone**), OR
- Autonomous mode triggers Iron Law #22 auto-defeat.

Both modes. At ship, remaining envelope is logged on the leaderboard for post-mortem.

## #22 Defeat / pivot protocol is deterministic
**Mechanism:** When `autonomous.yaml` is present (autonomous mode) the `plateau_threshold` and `exhaustion_threshold` fields define mechanical pivot and defeat rules. When absent (interactive mode) the *same thresholds* propose a decision to the user but do not act. Rules:
- **Auto-pivot**: after `plateau_threshold` (default 3) consecutive vN with no stat-significant CV improvement (Welch's t on seed-mean leaderboard), orchestrator consults `coverage.json`, picks the highest-leverage unexplored `pattern_area`, opens v(N+1) with that area's brainstorm pre-seeded, and appends `auto-pivot` to `events_history`. No user prompt required in autonomous mode.
- **Auto-defeat**: when `coverage.json` shows all pattern areas marked `ceiling_reason ∈ {approach-exhausted, feature-limited, intrinsic}` OR `plateau_threshold × 2` consecutive plateaus across all areas, orchestrator writes `disproven/surrender-vN.md` (template: [templates/surrender-card.md](templates/surrender-card.md)) with ceiling evidence, sets `state.phase = ABORTED`, emits final report, and stops. No further runs without explicit user `reset-surrender` command.
- **Fallback**: in interactive mode the orchestrator emits a proposal artifact `audits/vN-pivot-proposal.md` and waits. Same thresholds, different actor.

This law is how long-horizon autonomy stays bounded: every exploration terminates in either a ship, a pivot, or a surrender-card — never in drift.

## #23 Anti-Goodhart: secondary metrics are monitored, not optimized
**Mechanism:** `plans/vN.md` pre-registration must list ≥2 `secondary_metrics` from [checklists/anti-goodhart.md](checklists/anti-goodhart.md) (e.g., calibration-ECE, worst-segment-score, prediction-entropy, class-parity-gap, per-feature-stability). Every run logs values via `scripts/tracker_log.py` to the leaderboard `secondary_metrics` field. Ship-gate refuses if any secondary degraded >2σ from the feature-baseline value, even when primary improved. Iron Law #14 narrative audit extends: any top feature that improves primary but worsens a secondary must be acknowledged in `audits/vN-narrative.md` §4 "Goodhart risk". Secondary list is pre-registered at FRAME; *adding* across versions is allowed, *removal* requires Iron Law #24 override (`law=anti-goodhart-shrink`). Applies in both modes.

## #24 Overrides are first-class artifacts, not loopholes
**Mechanism:** Any relaxation of any iron law requires `ds-workspace/overrides/vN-override-<law>.md` using [templates/override-card.md](templates/override-card.md) with YAML frontmatter `{law, scope: run|version|permanent, reason, expected_risk, mitigation, expires_at, signed_by}`. `consistency_lint.py` fails any gate proceeding past the affected law's checkpoint without this artifact. `state.active_overrides` enumerates active ids.

At ship-gate:
- `scope=run|version` overrides expire at SHIP (auto-cleared).
- `scope=permanent` overrides require re-authorization — Council quorum in autonomous mode, user sign-off in interactive.
- **Core laws (#1, #12, #16, #17, #20, `law=budget`)** require `user` in `signed_by` at **any scope** — Council never substitutes.
- **Laws #16 and #20** reject `scope=permanent` outright (linter hard-fails regardless of signers; use `scope=run` + re-lock plan).

Applies in both modes. This is how "exceptions prove the rule" becomes filesystem-verifiable.

## #25 Coverage-driven exploration: brainstorm on novelty, not on schedule
**Mechanism:** `ds-workspace/coverage.json` (schema: [templates/coverage.schema.json](templates/coverage.schema.json)) tracks, per `pattern_area ∈ {data-quality, feature-engineering, model-selection, ensemble, ml-classification, idea-research, …}`: `{approaches_tried: [], ceiling_reason, last_tried_vN, remaining_leverage_estimate ∈ [0,1], exhausted: bool}`. Brainstorm-before-build (formerly Iron Law #19a phase-driven) is now *novelty-driven*:
- A brainstorm file (template: [templates/brainstorm-vN.md](templates/brainstorm-vN.md), ≥3 alternatives) is required when entering a pattern area with `approaches_tried == []` OR when the chosen approach family is not among the logged `approaches_tried`.
- If the chosen approach has already been tried and logged with a `ceiling_reason`, no new brainstorm required — but the prior brainstorm and its outcome are cited in the run's `notes_ref`.
- Legacy per-phase brainstorms (DATA_PREP, FEATURE_MODEL, FEATURE_ENG, TUNING) are preserved as *default triggers on v1* but are dropped for v≥2 when `coverage.json` shows the area already explored.
- `coverage.json` is updated at every VALIDATE exit by the orchestrator (new approaches appended; `ceiling_reason` written on exhaustion).
- `consistency_lint.py` refuses SHIP if `coverage.json` is missing, malformed, or has unexplored high-priority pattern areas without a documented reason (warning, not error, in daily mode; error in competition mode).

This replaces the implicit "brainstorm every phase every version" cadence with an explicit novelty gate. The filesystem artifact is `coverage.json`; the brainstorm file is the proof that novelty was addressed.

---

## Enforcement pattern (common to all rules)

Phase transitions happen only when required files exist and have been signed. Persona output IS the signature. A gate is a checklist file; a sign-off is the filesystem-visible write of that checklist with the persona name filled in. This is mechanical, not advisory. In daily mode, some persona sign-offs are advisory rather than blocking (see mode comparison table in [SKILL.md](SKILL.md)), but the mechanical enforcement of required gates is identical.

## Autonomous mode layer

When `autonomous.yaml` is present at workspace root, the following substitutions replace human gates:
- User-typed `ship` → auto-ship when all gate criteria PASS AND `autonomous.yaml.ship_target` is met.
- User-typed `pivot or ship` proposal → auto-pivot per Iron Law #22.
- Domain Expert sign-off on DGP memo → replaced by Literature Scout Full memo + Meta-Auditor sign-off (Iron Law #24 substitution declared in `autonomous.yaml.persona_substitutions`).
- Human override authorization → replaced by Council quorum (≥2/3 of dispatched Skeptic subagents with distinct priors agree). Council never auto-authorizes scope=`permanent` overrides of Iron Laws #1, #12, #16, #17, #20 or `law=budget` — these remain human-gated even in autonomous mode. (Iron Laws #16 and #20 additionally reject scope=`permanent` outright; use scope=run with a re-lock plan.) `consistency_lint.py` canonicalises slug and numeric law ids (e.g. `law: eval-harness` ≡ `law: "20"`) so the guard cannot be bypassed by alternate spelling.

Autonomous mode does NOT relax any iron law. It only replaces the *actor* of a human-gated step with a mechanical or council-based substitute, and every substitution is declared in `autonomous.yaml` and audited at ship. See [playbooks/autonomous-mode.md](playbooks/autonomous-mode.md).
