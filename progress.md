# Data Science Skill — Progress & Audit Log

---

## Context

This document tracks the iterative improvement of a data science skill (a governance harness for iterative modeling work). The conversation below was between Jay and a coding agent auditing and improving the skill.

**Key design intent of the skill:**
- It is a **harness**, not a specific modeling playbook — designed to let the best LLM explore for the best solution while being honest and producing real results instead of faking it.
- Optimized for **Kaggle-style competitions**, with plans to add a dual mode (competition vs. general daily work).
- Goal: constrain the LLM agent from being lazy, fooling itself, making bad mistakes, or losing track — while simultaneously pushing for maximum thinking, analysis, planning, and researcher-like creativity.

---

## Initial Audit Findings

> Jay's prompt: *"I want an audit and critique for this skill. From a real data scientist workflow perspective, how can this skill be helpful? Is it adding value? What is it missing?"*

### What's Genuinely Valuable
- **The DGP memo (Iron Law #12)** is the crown jewel. Forcing the analyst to write down the data-generating process — feature provenance, selection mechanism, confounds, expected feature directions — before touching a model is the single highest-value intervention. The §7a structured predictions block (pre-registering which features should matter and in which direction) is especially powerful.
- **Disproven-cards as first-class artifacts.** Treating "what didn't work and why" as a structured, versioned artifact with YAML frontmatter prevents teams from repeating mistakes and builds genuine institutional knowledge. The "museum of wrong ideas" on the dashboard is a great touch.
- **The adversarial validation pipeline** (`adversarial_validation.py`) is well-implemented — the AUC thresholds (0.55 / 0.60 / 0.75) are reasonable, the fallback from LightGBM to sklearn is practical, and feeding `adv_auc` into the expanded predicted interval formula is a clever way to quantify train/test drift rather than just flagging it.
- **The consistency linter** solves a real problem — cross-referencing YAML frontmatter across plans, findings, disproven-cards, DGP predictions, and the leaderboard at every gate.
- **One-shot submission discipline** with split internal/external ship gates is well-designed for competition settings.

### Where It Fell Short — Original Critiques
1. **Massive overhead for the common case** — 9 phases, 7 personas, 9 checklists, 8 abort events, 17 iron laws; no lightweight mode.
2. **Doesn't touch actual modeling** — no guidance on feature engineering, model selection, hyperparameter tuning, ensemble methods, missing data, or class imbalance.
3. **Persona system is self-referential theater** — all 7 personas played by the same LLM; sign-offs are performative.
4. **No data cleaning / preprocessing playbook** — skill jumps from FRAME to DGP to AUDIT to EDA with no structured guidance on wrangling messy data.
5. **No experiment tracking integration** — custom dashboard is a parallel universe to MLflow/W&B/Neptune.
6. **Literature Scout is underspecified** — no mechanically enforceable way to meet "≥5 sources" requirement; no reliable access to Kaggle/arXiv APIs.
7. **Missing interpretability beyond SHAP** — no PDP, ICE, permutation importance, segment-level weakness analysis.
8. **Iron Law numbering is broken** — laws jump from #15 to #17 then back to #16.
9. **No guidance on when to stop iterating** — "pivot" is mentioned but never defined.
10. **Competition-centric, weak on business DS** — no A/B test design, causal inference, stakeholder communication playbooks.

---

## Jay's Decisions on Critiques

| Critique | Decision |
|---|---|
| 1. Overhead / no lightweight mode | ✅ Add dual mode: competition mode and general daily work mode |
| 2. No actual modeling guidance | ✅ Keep as-is by design (harness, not recipe); address via brainstorming/exploration framework instead |
| 3. Persona theater | ✅ Move personas to subagent dispatch; mark automated gates as `automated: true` |
| 4. No data cleaning phase | ✅ Add DATA_PREP phase |
| 5. No experiment tracking | ✅ Add real MLflow/W&B logger (`tracker_log.py`) integrated with the dashboard |
| 6. Literature Scout underspecified | ✅ Tier the scout by what's available at runtime; add exa-search/deep-research setup prompts |
| 7. Missing interpretability | ✅ Expand to PDP, ICE, permutation importance; add segment-level weakness analysis; no counterfactuals needed |
| 8. Broken Iron Law numbering | ✅ Fix numbering |
| 9. No stop criteria | ⬜ Not explicitly addressed yet |
| 10. Business DS playbooks | ⬜ Deferred — can be a "sub-skill" later |

---

## Completed Work

### Round 1 — Core Improvements
**New files created (3):**
- `playbooks/phase-data-prep.md` — full DATA_PREP phase between AUDIT and EDA, covering schema audit, missing value census, duplicate detection, outlier assessment, type coercion, multi-table join strategy, and leakage-aware prep sign-off
- `checklists/model-diagnostics.md` — SHAP + PDP + ICE + permutation importance + segment-level weakness analysis + residual analysis + diagnostic-to-action mapping table
- `checklists/experiment-tracking.md` — MLflow and W&B integration setup and verification

**Files modified (20):**

| Change | Files touched |
|---|---|
| Dual mode (competition/daily) | `SKILL.md`, `loop-state-machine.md`, `phase-frame.md`, `slash/ds.md`, `README.md`, `templates/state.schema.json` |
| DATA_PREP phase | `SKILL.md`, `loop-state-machine.md`, `playbooks/phase-eda.md` (entry gate now references DATA_PREP), `workspace-layout.md`, `templates/finding-card.md`, `templates/step-journal.md`, `scripts/verify_skill_files.py` |
| Iron Law #18 (model diagnostics) | `iron-laws.md` (fixed #16/#17 ordering, added #18), `SKILL.md`, `playbooks/phase-feature-model.md` (added step 5 with full diagnostics), `checklists/narrative-audit.md` (added permutation cross-check, segment weakness review) |
| Personas as subagents | `SKILL.md` (rewrote "Parallel subagent dispatch" → "Persona dispatch via subagents"), all 7 persona files (added `## Dispatch` section) |
| Experiment tracking | `SKILL.md` (new section), `templates/state.schema.json` (added `tracker` and `tracker_config` fields) |
| State schema fixes | Added DGP, DATA_PREP, MERGE to phase enum; added missing events to events enum; added `mode` as required field |

---

### Round 2 — Persona Honesty, Tracker, & Literature Scout Tiers

**1. `automated: true` flag on all persona audits**
Every persona's output template now includes `automated: true`, `review_type: subagent | human`, and `confidence: high | medium | low`. Each persona has a tailored consumer note. The ship-gate checklist now requires these fields and recommends human co-review on Skeptic and Domain Expert for high-stakes gates.

**2. `scripts/tracker_log.py` — real MLflow/W&B logger**
A 280-line Python script that serves as the single entry point for recording runs. Always updates `leaderboard.json` atomically (dashboard-first), then mirrors to the configured tracker. Features: upsert logic, automatic artifact detection (plots directory, `metrics.json`, `ablation.md`), image auto-detection for W&B, pass-through of extra numeric fields, graceful degradation (tracker failure = exit 2, dashboard still updated). The FEATURE_MODEL playbook step 6 now calls `tracker_log.py` instead of manual JSON writes.

**3. Literature Scout tiered search with tool detection**
- **Tier 1** (always available): training knowledge + WebSearch. Sources tagged with provenance and confidence. Lower source counts (Lite ≥3, Full ≥10).
- **Tier 2** (exa-search or deep-research connected): citation-backed semantic search; every source has a URL. Full source counts (Lite ≥5, Full ≥15).
- **Tier 3** (human-assisted): Scout produces a structured search plan; user pastes back results.
- When running at Tier 1, the scout warns the user with install instructions for exa-search and deep-research. Memo template now declares `search_tier` and `search_tools_used`.

---

### Round 3 — Brainstorming, Progressive Planning & Feature Baseline (Tier 1 of Creativity Audit)

> Jay's prompt on creativity audit summary: *"The skill is currently about 70/30 in favor of constraint. Four targeted additions would move the balance closer to 50/50."*

**New templates:**
- `templates/brainstorm-vN.md` — universal ≥3-alternatives brainstorm template with frontmatter; mandatory at DATA_PREP entry, FEATURE_MODEL entry, feature-engineering, and tuning sub-steps. Includes a Skeptic micro-audit block.
- `templates/plan-updates-vN.md` — progressive plan log. Revisions appended at DATA_PREP / EDA / FEATURE_MODEL / VALIDATE exits, each citing a concrete triggering artifact. Closes with a summary block at VALIDATE exit that seeds the next FRAME.

**Explorer persona extended:**
- `personas/explorer.md` now lists DATA_PREP entry (advisory) and FEATURE_MODEL entry (advisory) invocations in addition to EDA. Each produces its own audit artifact (`audits/vN-explorer-data-prep.md`, `audits/vN-explorer-modeling.md`). Runs as an independent subagent without seeing the orchestrator's preferred approach.

**Iron Law #19 added:**
- `iron-laws.md` — two-part coupled law: (a) brainstorm-before-build (≥3 alternatives documented for DATA_PREP, FEATURE_MODEL, and tuning; Skeptic micro-audit required at FEATURE_MODEL entry); (b) feature baseline (a `feature_baseline: true` row using raw features is required before engineered-feature runs; metrics report `feature_lift_vs_feature_baseline` and `tuning_lift_vs_default`).

**Playbooks updated:**
- `phase-data-prep.md` — added step 0 (raw-data baseline snapshot), step 0.5 (Explorer dispatch), rewrote step 2 to require per-column brainstorm; extended exit gate and persona invocations; added plan-updates requirement.
- `phase-feature-model.md` — added steps 0 (Explorer dispatch), 0.1 (model-family brainstorm with Skeptic micro-audit), 0.2 (feature-engineering brainstorm), 0.3 (tuning brainstorm); metrics now include `feature_lift_vs_feature_baseline` and `tuning_lift_vs_default`; extended exit gate.
- `phase-eda.md` — added step 5 (append plan-updates revision); exit gate enforces it.
- `phase-validate.md` — added step 7 (close plan-updates log with summary); exit gate enforces it.

**Governance docs updated:**
- `SKILL.md` — "18-law" → "19-law" throughout, extended persona-gate map, new brainstorm-before-build and progressive-planning section, new red-flag rows, Explorer and Skeptic-micro-audit added to dispatch pattern.
- `loop-state-machine.md` — entry gates extended; state-diagram labels updated.
- `README.md` — 19-law, brainstorm + feature-baseline + progressive-plan-log in features; layout shows new files.
- `workspace-layout.md` — new tree entries for `plans/vN-updates.md`, `runs/vN/data_baseline.txt`, `runs/vN/brainstorm-vN-*.md`, `audits/vN-explorer-*.md`, extended `metrics.json` fields.
- `scripts/verify_skill_files.py` — adds `brainstorm-vN.md` and `plan-updates-vN.md` to required files. Verifier passes (OK: all required files present).

---

## In Progress

### Round 4 — Tier 2 & Tier 3 of Creativity Audit

Jay's instruction: *"Make sure you completed everything in Tier 1, and then start Tier 2 and 3."*

Tier 1 was verified complete (`verify_skill_files.py` passes with OK). Tier 2 and Tier 3 are now in progress.

#### Tier 2 (High-Impact) — Complete
- [x] **Data-prep brainstorm step**: already in `phase-data-prep.md` step 2; exit gate confirmed coherent once learnings.md template landed.
- [x] **`runs/vN/tuning-plan.md` artifact**: template was already complete; wired into `phase-feature-model.md` step 0.3 + exit gate, `loop-state-machine.md` FEATURE_MODEL gate, `workspace-layout.md`, `verify_skill_files.py`.
- [x] **Cross-persona debate template** at DGP exit and SHIP: `templates/persona-debate.md` created; `phase-dgp.md` step 5b added; `checklists/ship-gate.md` debate block added; `loop-state-machine.md` DGP + SHIP gate rows updated; `SKILL.md` persona-gate map updated.
- [x] **`runs/vN/learnings.md`** — `templates/learnings-vN.md` created (append-only per-phase belief-update log); seeded at init; wired into EDA/FEATURE_MODEL/VALIDATE exit gates; `workspace-layout.md` updated; `verify_skill_files.py` updated; `templates/dgp-memo.md` §6 updated to reference it as primary empirical input for v(N+1).
- [x] **Bonus fix**: `tests/fixtures/state_valid.json` was missing required `mode` field (schema updated in Round 1 but fixture not updated); fixed, all 7 tests now pass.

#### Tier 3 (Polish) — Complete

**Gap analysis vs. `othmanadi/planning-with-files`:** That repo implements hook-based attention anchoring (UserPromptSubmit surfaces current plan state; Stop checks completion). We adopted this pattern; rejected their fragile JSONL session-catchup approach in favor of a structured step-journal reboot table.

- [x] **Extend consistency linter** (`scripts/consistency_lint.py`) with 8 new checks:
  - Iron Law #19 errors: `check_brainstorm_count`, `check_feature_baseline_present`, `check_tuning_has_default_params`
  - Tier 3 warnings: `check_single_path_resolution`, `check_lit_technique_ignored`, `check_silent_plan_log`, `check_learnings_incomplete`, `check_explorer_count`
- [x] **Standardize Explorer output contract** (`personas/explorer.md`) — formal YAML frontmatter schema with per-invocation minimum bars table and structured C-0N candidate sections.
- [x] **Add `novel-feature-flag`** (`playbooks/event-novel-modeling-flag.md` appended; `templates/state.schema.json`, `loop-state-machine.md`, `iron-laws.md` §7, `SKILL.md`, `playbooks/phase-feature-model.md` step 0.2 all updated).
- [x] **Extend `leaderboard.schema.json`** with 5 new run-level fields: `feature_baseline`, `default_params`, `tuning_run`, `feature_lift_vs_feature_baseline`, `tuning_lift_vs_default`; fixture updated; all 7 tests pass.
- [x] **Hook scripts** (`scripts/hooks/ds-state-surface.sh` — UserPromptSubmit; `scripts/hooks/ds-phase-check.sh` — Stop); registered in `verify_skill_files.py`; hook setup section added to `SKILL.md` with JSON config snippet and security boundary docs.
- [x] **Session reboot block** added to top of `templates/step-journal.md` (5-question orientation table + instructions for filling it from `state.json`).

---

## Deferred / Future Work

- Business DS sub-skill (causal inference, A/B test design, cost-sensitive evaluation, stakeholder reporting) — deferred, can be its own sub-skill.
- Define "pivot" criteria when stop rule (3 consecutive vN with no stat-significant CV improvement) fires.
