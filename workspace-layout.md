# Workspace Layout (`ds-workspace/`)

Per-project, created at run start in the current project root. Never auto-pruned.

```
<project-root>/ds-workspace/
├── state.json                  # see templates/state.schema.json (includes mode: competition|daily, tracker config)
├── USER_GUIDANCE.md            # user intent anchor — read before lessons.md / iron-laws each response
├── data-contract.md
├── holdout/
│   ├── HOLDOUT_LOCK.txt        # sha256 + lock timestamp + DO NOT READ notice
│   └── holdout.parquet
├── plans/vN.md                 # structured plan with YAML pre-registration, frozen at FRAME exit
├── plans/vN-updates.md         # progressive plan log — revisions appended at DATA_PREP/EDA/FEATURE_MODEL/VALIDATE exits (Iron Law #19)
├── findings/vN-fNNN.md
├── disproven/vN-dNNN.md        # first-class learning artifacts
├── overrides/                  # permanent-scope user overrides (templates/user-override.md)
│   └── vN-override-NNN.md
├── literature/vN-memo.md
├── step-journal/vN.md          # append-only COT + decision log per version
├── lessons.md                  # rolling consolidated lessons across all versions
├── nb/vN_sandbox.ipynb         # seeded from templates/sandbox-vN.ipynb
├── audits/
│   ├── vN-skeptic.md
│   ├── vN-leakage.md
│   ├── vN-cv-scheme.md
│   ├── vN-data-prep.md         # data cleaning/prep decisions (DATA_PREP phase)
│   ├── vN-explorer-data-prep.md # Explorer advisory brainstorm at DATA_PREP entry (Iron Law #19)
│   ├── vN-explorer.md          # Explorer EDA hypotheses
│   ├── vN-explorer-modeling.md # Explorer advisory brainstorm at FEATURE_MODEL entry (Iron Law #19)
│   ├── vN-model-diagnostics.md # PDP, ICE, SHAP, permutation importance, segment analysis (Iron Law #18)
│   ├── vN-assumptions.md
│   ├── vN-repro.md
│   └── vN-ship-gate.md
├── runs/vN/
│   ├── data_baseline.txt       # raw-data snapshot from DATA_PREP step 0 (pre-prep reference)
│   ├── brainstorm-vN-DATA_PREP.md    # ≥3 handling strategies per >5%-missing col (Iron Law #19a)
│   ├── brainstorm-vN-FEATURE_MODEL.md # ≥3 model-family candidates, Skeptic micro-audited (Iron Law #19a)
│   ├── brainstorm-vN-FEATURE_ENG.md  # ≥2 feature representations per top hypothesis (Iron Law #19a)
│   ├── brainstorm-vN-TUNING.md       # hyperparameter tuning brainstorm (if tuning performed, Iron Law #19a)
│   ├── tuning-plan.md          # tuning plan (params, ranges, strategy, nested-CV wiring, Skeptic-signed; if tuning performed)
│   ├── learnings.md            # within-version belief-update log, appended at each phase exit; feeds DGP §6 of v(N+1)
│   ├── metrics.json            # CV mean/std, CI, lift_vs_baseline, feature_lift_vs_feature_baseline, tuning_lift_vs_default, baseline/feature_baseline flags
│   ├── ablation.md             # feature-group lift, references brainstorm alternatives tried/dropped
│   ├── env.lock
│   ├── seed.txt
│   ├── data.sha256
│   └── plots/                  # includes PDP, ICE, SHAP, calibration, segment plots
├── nb/                          # notebook track
│   └── vN_*.ipynb               # must only call src/
├── src/                         # library code
│   └── data/ features/ models/ evaluation/
└── dashboard/                   # seeded from skill's dashboard-template/
    ├── index.html
    ├── assets/...
    └── data/
        ├── leaderboard.json
        └── events.ndjson
```

## Initialization procedure

1. `mkdir -p` the tree above.
2. Copy contents of `$SKILL/dashboard-template/` into `ds-workspace/dashboard/`.
3. Write initial `state.json` conforming to `$SKILL/templates/state.schema.json`.
4. Write initial `data/leaderboard.json` conforming to `$SKILL/templates/leaderboard.schema.json` with empty `runs` array.
5. Copy `$SKILL/templates/lessons.md` to `ds-workspace/lessons.md`.
6. Copy `$SKILL/templates/user-guidance.md` to `ds-workspace/USER_GUIDANCE.md`.
7. Create `ds-workspace/overrides/` directory.
8. Create `ds-workspace/step-journal/` and seed `v1.md` from `$SKILL/templates/step-journal.md`.
9. Seed `ds-workspace/nb/v1_sandbox.ipynb` from `$SKILL/templates/sandbox-vN.ipynb`.
10. Start server via `$SKILL/server/serve_dashboard.py` pointing at `ds-workspace/dashboard/`.

## Consistency gate

Before any phase transition past FINDINGS (and before MERGE and SHIP), run:

```
python $SKILL/scripts/consistency_lint.py ds-workspace
```

Exit 0 is required. Errors block the gate. Warnings are surfaced on the dashboard's Consistency panel (see `dashboard-spec.md`) so the agent keeps a **rolling window of aligned knowledge** — every new finding, journal entry, and lesson is cross-checked against every prior claim, and contradictions are flagged before they quietly fork the narrative.

## Retention

Orchestrator never auto-deletes. Runs may transition status (`valid` → `superseded` | `invalidated`) but stay on disk. User manually prunes.

## Promotion target

Generalizable lessons from `disproven/` or `findings/` are promoted (with Skeptic + Statistician sign-off) to:

```
~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<lesson-slug>.md
```
