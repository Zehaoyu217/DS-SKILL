# Phase: FEATURE_MODEL

## Entry gate
EDA exited AND at least one entry in `runs/*/metrics.json` tagged `baseline: true` exists (the model baseline — Iron Law #5) AND at least one run tagged `feature_baseline: true` exists (raw-feature run — Iron Law #19) AND `audits/vN-adversarial.md` is present (from the adversarial-validation step in AUDIT) AND `runs/v{N}/brainstorm-v{N}-FEATURE_MODEL.md` exists with ≥3 model-family candidates brainstormed AND Skeptic has signed a micro-audit on that brainstorm. If `novel-modeling-flag` is active, also requires `literature/vN-memo.md` in Full mode.

**Eval harness lock check (Iron Law #20):** Run before any modeling work:
```
python $SKILL/scripts/hash_eval_harness.py <ds-workspace> --check
```
Exit 1 fires the `eval-harness-tampered` event and blocks this phase until the user invokes `override eval-harness <reason>`.

## Purpose
Implement features and models, run cross-validation with proper uncertainty and multi-seed stability, maintain leaderboard integrity, and confirm no new leakage patterns emerge during implementation. Hyperparameter tuning respects nested CV. Every candidate above baseline records an ablation. Feature engineering is tracked as a first-class step with its own baseline and brainstorm, so "did engineering help?" is answerable separately from "did this model family help?".

## Brainstorm precedence (Iron Law #25 over #19a)

At **v=1**, Iron Law #19a applies unconditionally: every brainstorm step below
(0.1 model family, 0.2 feature engineering, 0.3 tuning) requires ≥3 alternatives.

At **v≥2**, read `coverage.json` first (Iron Law #25). Map each brainstorm step to a
pattern area: 0.1 → `model-selection`, 0.2 → `feature-engineering`, 0.3 → `hyperparameter-tuning`,
and the optional ensembling path → `ensemble`. For each area:
- If `exhausted: true` with a documented `ceiling_reason`, the corresponding brainstorm is
  skipped — orchestrator records `coverage-exhausted` in place of the new-file path and
  advances. The prior version's winning candidate is the default for that axis.
- If not exhausted, run the full ≥3 brainstorm AND update that area's `approaches_tried`
  in `coverage.json` at VALIDATE exit.
- If ALL top-priority pattern areas are exhausted, `auto-defeat` fires (Iron Law #22)
  rather than permit empty brainstorm entries.

The consistency linter reads `coverage.json` and refuses to accept a skipped brainstorm
without the exhaustion citation. Steps 0 and 0.15 (Explorer dispatch, pre-screen) are
mandatory regardless of coverage state — they are mechanical, not brainstorm-gated.

## Steps (in order)

0. **Explorer dispatch (advisory, non-blocking).** Launch Explorer as an independent subagent with the literature memo and the EDA hypotheses but *without* the orchestrator's preferred approach. Explorer writes `audits/v{N}-explorer-modeling.md` with ≥3 unusual / creative candidates (novel stacking configurations, cross-domain analogies, unusual feature representations, unconventional hyperparameter regions). Feeds the brainstorm in step 0.1.

0.1. **Model-family brainstorm.** Write `runs/v{N}/brainstorm-v{N}-FEATURE_MODEL.md` using [templates/brainstorm-vN.md](../templates/brainstorm-vN.md) with ≥3 candidate model families, each with (a) pros/cons for this problem, (b) literature refs from `literature/v{N}-memo.md` or documented memo-silence, (c) expected effect size, (d) compute/reproducibility cost. Pick top-2 to implement (chosen + contingency). Dispatch Skeptic for a required micro-audit on this file — Skeptic's verdict (`accept | accept-with-caveats | request-rework`) is appended in the Skeptic-micro-audit section of the brainstorm.

0.15. **Candidate pre-screen (two-tier filter).** Before committing to full K-fold ceremony for each brainstorm candidate, run a cheap 1-fold CV to eliminate obvious losers.

   **Procedure:**
   1. Record the screen seed in `runs/v{N}/screen-seed.txt` (use a fixed value, e.g. `42`, for reproducibility).
   2. For each candidate in `brainstorm-v{N}-FEATURE_MODEL.md`, run a **1-fold CV on 50% of training data** (subsampled with the screen seed). For **temporal CV schemes**, use the terminal fold (most recent training slice → next time window) rather than a random subsample.
   3. Pass/fail threshold: `screen_cv_1fold >= feature_baseline_cv_mean - 2 × feature_baseline_cv_std`. *(This is intentionally permissive — it filters only obvious losers. Known choice; can be revisited.)*
   4. Write results to `runs/v{N}/screen-results.json`:
      ```json
      {
        "screen_date": "...",
        "screen_seed": 42,
        "screen_n_rows": <50% of train>,
        "screen_n_folds": 1,
        "threshold": <feature_baseline_cv_mean - 2*cv_std>,
        "threshold_formula": "feature_baseline_cv_mean - 2 * feature_baseline_cv_std",
        "candidates": [
          {"id": "A1", "cv_1fold": 0.823, "passed": true},
          {"id": "A2", "cv_1fold": 0.611, "passed": false, "rejection_reason": "below_threshold"}
        ]
      }
      ```
   5. Candidates that fail are **not silently dropped** — they are recorded with `"passed": false` in `screen-results.json` and their id is added to `rejected_alternative_ids` in the brainstorm file with note `"screen-rejected"`.
   6. **Edge case:** If ALL candidates fail the screen, do not proceed automatically — surface this to the user. The feature_baseline itself may be a local maximum, or the screen threshold may need adjustment.
   7. The pre-screen applies **only to the model-family brainstorm** (step 0.1). It does NOT apply to the DATA_PREP brainstorm (no CV signal exists for data handling strategies) or the feature-engineering brainstorm (step 0.2 runs only on passing model-family candidates).

   This step does not replace the full K-fold ceremony — it is a coarse pre-filter. All passing candidates still run the full ceremony in steps 1–10.

0.2. **Feature-engineering brainstorm.** Write `runs/v{N}/brainstorm-v{N}-FEATURE_ENG.md` with ≥2 feature-representation alternatives per top hypothesis (raw / binned / log-transformed / interaction / domain-specific aggregation / embedding). Mark which representations were already tried in the `feature_baseline` run so we don't reinvent raw features. Advisory Skeptic review is optional here. **If any proposed representation is outside the standard set `{raw, binned, log-transform, interaction, aggregation, categorical-encoding, embedding}`, fire `novel-feature-flag`** — see [event-novel-modeling-flag.md](event-novel-modeling-flag.md#event-novel-feature-flag) for the response protocol (requires Full Literature Scout memo before step 1 continues).

0.3. **Tuning-plan brainstorm + plan** (required if any hyperparameter search will be performed in this version). Two paired artifacts:
   - **Brainstorm** (`runs/v{N}/brainstorm-v{N}-TUNING.md`): exploratory alternatives for search strategy and hyperparameter regions. ≥3 candidates per the brainstorm template. Feeds the plan.
   - **Tuning plan** (`runs/v{N}/tuning-plan.md`): the authoritative execution artifact, written from [templates/tuning-plan-vN.md](../templates/tuning-plan-vN.md). Contains: parameter space table with literature-informed range bounds, search strategy, nested-CV wiring description, stopping rules, multi-seed confirmation plan, and pre-registered rejection criteria. Skeptic must sign §4 (nested-CV wiring) before any tuned run is executed. Without Skeptic sign-off on this section, the tuning result cannot be promoted to the leaderboard.

0.4. **Mini-loop hill-climbing** (optional accelerator — invoke with `mini-loop` command or when the brainstorm has one clear winner to refine).

   The mini-loop runs an autoresearch-style inner iteration over the **winning candidate from step 0.15** (or the top-ranked passing candidate if no clear winner). It hill-climbs configuration choices (feature representation swap, hyperparameter region shift, model variant) using cheap 3-fold CV before promoting the winner to full K-fold ceremony. This is an accelerator, not a new brainstorm — all candidates must trace back to a brainstorm entry.

   **Termination (configurable):** Defaults K=3 consecutive non-improvements, max=15 total iterations. Set in `plans/vN.md` under `pre_registration.mini_loop_k` and `pre_registration.mini_loop_max_iter`. Termination fires on whichever condition occurs first.

   **Improvement criterion:** `cv_mean_3fold > current_best_cv_mean + 0.5 × cv_std` (beat current best by more than half a standard deviation on the 3-fold signal). Reset non-improvement counter on improvement; increment on tie or regression.

   **Procedure per iteration:**
   1. Make one targeted change to the current best configuration (within brainstorm-approved option space).
   2. Run 3-fold CV (cheap signal). Record result in `runs/v{N}/mini-loop/iteration-NNN/metrics.json` with `"mini_loop": true, "provisional": true`.
   3. Log as a **provisional** entry in `leaderboard.json` (status `"provisional"`, rendered muted/dashed in dashboard). **Do NOT call `log_run_commit.sh`** for provisional iterations.
   4. Apply improvement criterion. If improved: update current best, reset counter. If not: increment counter.
   5. If termination condition fires: exit loop, write `runs/v{N}/mini-loop/winner.json` (see schema below).

   **Winner record** (`runs/v{N}/mini-loop/winner.json`): required fields
   `winner_iteration`, `winner_cv_3fold`, `winner_cv_std`,
   `starting_candidate_id`, `total_iterations`,
   `non_improvement_streak_at_stop`, `termination_reason` (one of
   `k_non_improvements | max_iterations`), `skeptic_signoff` (`pending |
   signed`), `skeptic_note` (may be empty until sign-off).

   **Post-loop Skeptic sign-off:** Dispatch Skeptic **once** on the winner (not on individual iterations). Skeptic checks: (a) winner's configuration is within the option space the step 0.1 brainstorm justified, (b) no suspicious jump from last-to-winner relative to the 3-fold variance, (c) the change is coherent with DGP §7a expectations. Skeptic appends verdict to `winner.json` (`skeptic_signoff: signed`). `request-rework` blocks advancement to step 1.

   **After sign-off:** The winner configuration advances to steps 1–9 (full K-fold ceremony). Provisional leaderboard entries from mini-loop iterations are marked `"status": "provisional-retired"` once the full run is logged.

   **Note on new candidates:** If during the mini-loop the Engineer wants to try a configuration not traceable to a brainstorm entry, the loop must pause, the brainstorm updated and re-audited, before continuing. The mini-loop does not bypass the brainstorm requirement.

1. Implement features in `src/features/` and models in `src/models/` following the CV scheme from FRAME (revised if AUDIT fired `covariate-shift`) and the chosen alternatives from steps 0.1–0.3.
2. Run cross-validation. If any hyperparameter tuning is performed, it runs inside an outer CV fold (nested CV) OR the reported `cv_mean` is explicitly discounted for optimization bias (see [encoding-audit.md](../checklists/encoding-audit.md) nested-CV section). If tuning is performed, the default-params reference run is logged first as a separate leaderboard row, and every tuned run reports `tuning_lift_vs_default` in addition to `lift_vs_baseline`.
3. Record results in `runs/vN/metrics.json` with fields: `cv_mean`, `cv_std`, `cv_ci95`, `lift_vs_baseline`, `feature_lift_vs_feature_baseline`, `tuning_lift_vs_default` (if applicable), `seeds: [list]`, `seed_std`, `baseline: false` (set to `true` only for model baseline), `feature_baseline: false` (set to `true` only for raw-feature run, Iron Law #19). At least one run per candidate uses ≥3 seeds; seed-to-seed std is reported.
4. **Ablation log.** For every candidate with `lift_vs_baseline > 0`, record which feature group was added and the per-feature-group CV delta in `runs/vN/ablation.md`. The ablation must reference the feature-brainstorm entries from step 0.2 (which representation alternatives were tried, which was dropped, why). Feature groups with 0 ± noise lift are candidates for removal (and emit disproven-cards if removed).
5. **Model diagnostics** (Iron Law #18). Run [checklists/model-diagnostics.md](../checklists/model-diagnostics.md) on every candidate above baseline:
   - SHAP values (global summary + 3 high-confidence / 3 low-confidence local explanations)
   - Partial dependence plots (PDP) for top-10 features; 2D PDP for top-3 suspected interactions
   - ICE plots for top-5 features (check for heterogeneity)
   - Permutation importance (≥5 repeats) — compare ranking against SHAP ranking
   - Segment-level weakness analysis: bin continuous features into quantiles, compute validation metric per bin; for categoricals, compute metric per category. Flag segments >1σ below overall.
   - Residual analysis: residuals vs. predicted, residuals vs. top features, calibration curve
   - Write results to `audits/vN-model-diagnostics.md` and plots to `runs/vN/plots/`
6. **Log the run** via `python $SKILL/scripts/tracker_log.py ds-workspace runs/vN`. This atomically updates `leaderboard.json`, appends to `events.ndjson`, and (if configured) mirrors to MLflow/W&B. See [checklists/experiment-tracking.md](../checklists/experiment-tracking.md).

6a. **Git-commit the run artifacts** (Iron Law #4 extension — run is git-anchored):
    ```
    bash $SKILL/scripts/log_run_commit.sh ds-workspace runs/vN <run-id> "<description>"
    ```
    This commits `metrics.json`, `ablation.md`, `plots/`, and `leaderboard.json` under a structured `ds-run:` message and patches `commit_sha` back into the leaderboard record. Skip this step only if the project is not a git repo (script exits 0 with a warning in that case). **Do NOT call this step for mini-loop provisional iterations** — only for promoted full-ceremony runs.
7. Engineer sanity-check: verify presence of `env.lock`, `seed.txt`, `data.sha256` in `runs/vN/`.
8. Validation Auditor re-runs [checklists/leakage-audit.md](../checklists/leakage-audit.md) and [checklists/encoding-audit.md](../checklists/encoding-audit.md) on new code in `src/`.
9. If any candidate triggers `suspicious-lift` heuristics (see [event-suspicious-lift.md](event-suspicious-lift.md)), freeze it as `invalidated: suspected` and fire the event.

## Persona invocations
- **Explorer** (entry, advisory): Produce `audits/v{N}-explorer-modeling.md` with ≥3 unusual candidates before step 0.1 brainstorm.
- **Skeptic** (entry, required micro-audit): Review `runs/v{N}/brainstorm-v{N}-FEATURE_MODEL.md`. Appends verdict + notes to the brainstorm's Skeptic-micro-audit section. `request-rework` blocks the phase from advancing to step 1.
- **Engineer** (primary): Implement features/models, run CV (nested where tuned), populate metrics, record seeds, maintain the three brainstorm files from steps 0.1–0.3. Output: code in `src/`, metrics in `runs/vN/metrics.json`, ablation notes in `runs/vN/ablation.md`, brainstorm files.
- **Validation Auditor** (mid-phase): Re-grep `src/` for leakage and encoding-audit patterns on new code. Output: findings in `audits/vN-leakage.md` and `audits/vN-encoding.md`.
- **Literature Scout** (if `novel-modeling-flag` active and Full memo not yet present): Produce `literature/vN-memo.md` in Full mode.

## Exit gate
All of the following must be true:
- **Leaderboard (#11):** current run present in `leaderboard.json`; no
  active leakage or encoding-audit patterns.
- **Metrics:** `cv_std` or `cv_ci95` reported; winner reports
  `feature_lift_vs_feature_baseline` (#19) and (if tuned)
  `tuning_lift_vs_default`.
- **Diagnostics (#18):** `audits/vN-model-diagnostics.md` present.
- **Ablation:** log present for the winning candidate, referencing the
  feature-brainstorm alternatives tried / dropped.
- **Brainstorms Skeptic-signed:** `brainstorm-v{N}-FEATURE_MODEL.md` and
  (if tuning was performed) `brainstorm-v{N}-TUNING.md` +
  `tuning-plan.md` §4 (nested-CV wiring).
- **Default-params baseline on leaderboard** when any tuning was run.
- **No unresolved `suspicious-lift`.**
- **Plan log:** `plans/v{N}-updates.md` has a revision block appended
  summarising which candidates survived and which were dropped.
- **Learnings log:** `runs/v{N}/learnings.md` has an entry per major
  candidate result or surprising ablation (not a single global entry).
- **Git anchor:** if the project is a git repo, the winner's leaderboard
  record has `commit_sha` populated (step 6a).

## Events that can abort this phase
- `leakage-found` (Validation Auditor grep hits a new pattern; mark runs invalidated and open v(N+1))
- `novel-modeling-flag` (if not yet flagged and fires now; require Full lit memo before continuing)
- `suspicious-lift` (on any candidate that would be promoted; pauses promotion until resolved)
