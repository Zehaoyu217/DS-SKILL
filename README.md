# data-science-iteration

A Claude Code skill for running **suspicious-yet-creative** iterative data-science loops against messy data and one-shot competitions. The hard thing about this work isn't the model — it's not fooling yourself. This skill enforces the discipline that prevents it.

**Two modes:** Competition (full ceremony, one-shot submission) and Daily (lighter gates, faster iteration for general data science work).

**What it gives you**

- **19 Iron Laws** with mechanical enforcement (locked holdout, adversarial validation, narrative audit, model diagnostics, one-shot submission, consistency lint, brainstorm-before-build + feature baseline, …).
- **Gated phases** (FRAME → DGP → AUDIT → DATA_PREP → EDA → FEATURE_MODEL → VALIDATE → FINDINGS → MERGE → SHIP) with persona sign-offs via independent subagents.
- **Data preparation phase** — systematic data cleaning, missing value handling, outlier assessment, and type coercion before any EDA or modeling.
- **Brainstorm-before-build** (Iron Law #19a) — at DATA_PREP and FEATURE_MODEL entries, a brainstorm file with ≥3 candidate approaches + rejected alternatives + contingency is required. Explorer subagent seeds it with creative / domain-specific candidates. Skeptic micro-audits the model-family brainstorm.
- **Feature baseline** (Iron Law #19b) — a `feature_baseline: true` row (raw, un-engineered features) is required before any engineered-feature run. Candidates report `feature_lift_vs_feature_baseline` separately from model-level lift. The same discipline applies to tuning (default-params reference run before tuned runs).
- **Progressive plan log** — `plans/v{N}-updates.md` records how the plan evolved within a version in response to learnings, with revision blocks appended at DATA_PREP / EDA / FEATURE_MODEL / VALIDATE exits. Preserves the thinking trail instead of rewriting the plan in place.
- **Model diagnostics** (Iron Law #18) — SHAP, PDP, ICE, permutation importance, segment-level weakness analysis, and residual analysis. Understand *where* the model works and fails, not just its aggregate score.
- **Parallel branches** `vN.a / vN.b / vN.c` that merge deterministically on `cv_mean − 2·cv_std`.
- **Rolling knowledge loop** — structured-claim YAML blocks on every artifact + `consistency_lint.py` cross-references plan / DGP / findings / disproven / step-journal / lessons / leaderboard and fails any gate on contradictions.
- **Unified live dashboard** — leaderboard, museum of wrong ideas, consistency panel, rolling lessons, updates every 3 seconds.
- **Persona independence** — every persona (Skeptic, Validation Auditor, Statistician, Engineer, Domain Expert, Explorer, Literature Scout) runs as an independent Claude Code subagent, providing genuine review independence.
- **Experiment tracking** — optional MLflow or Weights & Biases integration alongside the built-in dashboard.
- **Split ship** — `internal-ship` (read locked holdout once) vs `external-submit` (organizer's hidden test, one submission, sha256-logged). In daily mode, ship is internal-only.

## Install

### Global (available to all projects)

```bash
cp -R data-science-iteration ~/.claude/skills/
```

Then from any project folder:

```bash
python3 ~/.claude/skills/data-science-iteration/scripts/init_workspace.py
```

Or from inside Claude Code:

```
/ds-init
```

### Project-level (checked into the repo)

```bash
mkdir -p .claude/skills
cp -R data-science-iteration .claude/skills/
```

From that project's root:

```bash
python3 .claude/skills/data-science-iteration/scripts/init_workspace.py
```

Project-level install pins the skill version to the repo; good for reproducibility and team-wide discipline.

### Python dependencies

- `pyyaml` (consistency linter)
- `pandas`, `numpy`, `scikit-learn` (adversarial validation + submission check)
- `lightgbm` (optional; falls back to `sklearn.ensemble.GradientBoostingClassifier`)

```bash
pip install pyyaml pandas numpy scikit-learn lightgbm
```

### JS tests (optional)

```bash
cd tests/dashboard && npm install
```

## Quick start

```bash
cd your-project-folder/      # contains data/ and docs/
/ds-init                     # creates ds-workspace/, starts dashboard
/ds                          # begin the loop — orchestrator asks 5 framing questions
```

Then follow the orchestrator: draft `plans/v1.md`, sign the DGP memo, enter the loop. Every phase transition runs the gate mechanics; you can't skip them.

## Layout after init

```
your-project-folder/
├── data/ …                                  # your inputs (unchanged)
├── docs/ …                                  # your inputs (unchanged)
└── ds-workspace/
    ├── state.json                           # current phase / version / mode / submission state
    ├── data-contract.md                     # fill during FRAME
    ├── plans/v1.md                          # structured plan with YAML pre-registration (frozen at FRAME exit)
    ├── plans/v1-updates.md                  # progressive plan log — revisions at DATA_PREP/EDA/FEATURE_MODEL/VALIDATE exits
    ├── dgp-memo.md                          # signed before modeling
    ├── findings/v1-fNNN.md                  # structured-claim cards
    ├── disproven/v1-dNNN.md                 # first-class learning artifacts
    ├── literature/v1-memo.md                # Lite memo mandatory at every FRAME (competition) / recommended (daily)
    ├── audits/v1-*.md                       # per-phase audit trails (data-prep, model-diagnostics, explorer-*)
    ├── runs/v1/                             # metrics, seeds, env, data hashes, plots (PDP, ICE, SHAP, etc.)
    ├── runs/v1/data_baseline.txt            # raw-data snapshot from DATA_PREP step 0
    ├── runs/v1/brainstorm-v1-*.md           # per-phase brainstorms (DATA_PREP, FEATURE_MODEL, FEATURE_ENG, TUNING)
    ├── nb/v1_sandbox.ipynb                  # structured probe notebook
    ├── src/{data,features,models,evaluation}/
    ├── step-journal/v1.md                   # append-only COT log
    ├── lessons.md                           # rolling cross-version lessons
    ├── holdout/HOLDOUT_LOCK.txt             # DO NOT READ until ship
    └── dashboard/                           # live view: leaderboard + consistency + lessons
        ├── index.html
        └── data/{leaderboard.json, consistency.json, lessons.json, events.ndjson}
```

## Slash commands

| Command | Purpose |
|---|---|
| `/ds-init` | Bootstrap `ds-workspace/` in the current project. |
| `/ds` | Start or resume the loop. Subcommands: `status`, `ship`, `ship external`, `abort`, `force v+1 <reason>`, `dig <hypothesis>`, `fork <names>`, `merge`, `reset-submission`. |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/init_workspace.py` | Bootstrap `ds-workspace/`. |
| `scripts/consistency_lint.py` | Cross-file claim linter — required GREEN at FINDINGS/MERGE/SHIP. |
| `scripts/adversarial_validation.py` | Train-vs-test AUC + duplicate ratio + top drift features. |
| `scripts/check_submission_format.py` | Validate submission CSV against `sample_submission.csv`. |
| `scripts/tracker_log.py` | Log a run to dashboard + external tracker (MLflow/W&B). Single entry point. |
| `scripts/leakage_grep.sh` | Extended leakage pattern grep. |
| `scripts/verify_skill_files.py` | Self-check the skill install is complete. |

## Testing the skill itself

```bash
# verifier
python3 scripts/verify_skill_files.py

# linter smoke test (create a tiny fixture workspace)
python3 scripts/consistency_lint.py ds-workspace

# python tests
python3 -m pytest tests/ -q

# dashboard JS tests
cd tests/dashboard && npx vitest run
```

## Key docs

- [SKILL.md](SKILL.md) — skill frontmatter, entry flow, mode comparison, persona-gate map.
- [iron-laws.md](iron-laws.md) — 19 laws with enforcement mechanisms.
- [loop-state-machine.md](loop-state-machine.md) — phase transitions, events, abort conditions.
- [workspace-layout.md](workspace-layout.md) — directory contract.
- [dashboard-spec.md](dashboard-spec.md) — writer contract for the live dashboard.
- `personas/` — Skeptic, Validation Auditor, Statistician, Engineer, Domain Expert, Explorer, Literature Scout.
- `playbooks/` — one file per phase + one per abort event.
- `checklists/` — leakage, cv-scheme, assumption-tests, reproducibility, ship-gate, encoding, adversarial, narrative, submission-format, model-diagnostics, experiment-tracking.
- `templates/` — plan, plan-updates (progressive log), brainstorm (≥3-alternative framework), finding, disproven, DGP memo, literature memo, sandbox notebook, step-journal, lessons, state + leaderboard schemas.

## When to use

- One-shot Kaggle-style competitions with a hidden test set (→ competition mode).
- General data science work: exploration, analysis, recurring model builds (→ daily mode).
- High-stakes research modeling where not-overfitting matters more than speed.
- Any project where discipline and audit trails matter.

## When NOT to use

- Production MLOps / deploy / drift monitoring.
- AutoML bandit sweeps.
- Pure engineering tasks that happen to touch data.

## Compatibility (optional)

Compatible with but not required: `superpowers:brainstorming`, `python-patterns`, `python-testing`, `eval-harness`, `exa-search`, `deep-research`, `continuous-learning`, `superpowers:dispatching-parallel-agents`.

## License

Apache-2.0 (or the owning repo's license — replace as needed).
