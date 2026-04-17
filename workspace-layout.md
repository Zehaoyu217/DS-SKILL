# Workspace Layout (`ds-workspace/`)

Per-project, created at run start in the current project root. Never auto-pruned.

```
<project-root>/ds-workspace/
├── state.json                  # see templates/state.schema.json (includes mode: competition|daily, tracker config, active_overrides)
├── USER_GUIDANCE.md            # user intent anchor — read before lessons.md / iron-laws each response
├── data-contract.md
├── dgp-memo.md                 # data generating process memo — signed at DGP exit, read by every downstream phase
├── budget.json                 # Iron Law #21 — envelope declared at FRAME, decremented per run
├── coverage.json               # Iron Law #25 — map of pattern areas explored, ceiling reasons, remaining leverage
├── autonomous.yaml             # OPTIONAL — if present at <project-root>, switches to autonomous mode (see template)
├── holdout/
│   ├── HOLDOUT_LOCK.txt        # sha256 + lock timestamp + DO NOT READ notice
│   └── holdout.parquet
├── plans/vN.md                 # structured plan with YAML pre-registration (incl. secondary_metrics per Iron Law #23), frozen at FRAME exit
├── plans/vN-updates.md         # progressive plan log — revisions appended at DATA_PREP/EDA/FEATURE_MODEL/VALIDATE exits (Iron Law #19)
├── findings/vN-fNNN.md
├── disproven/vN-dNNN.md        # first-class learning artifacts
├── disproven/surrender-vN.md   # Iron Law #22 auto-defeat artifact (template: templates/surrender-card.md)
├── overrides/                  # first-class override artifacts (Iron Law #24, template: override-card.md)
│   └── vN-override-<law>.md    # every iron-law relaxation requires an artifact here
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
│   ├── vN-anti-goodhart.md     # secondary-metrics delta table (Iron Law #23)
│   ├── vN-pivot-proposal.md    # OPTIONAL — orchestrator-proposed pivot when plateau threshold hit (non-autonomous mode, Iron Law #22)
│   ├── vN-council-<issue>.md   # Council quorum artifact for Iron Law #24 overrides or ship authorization in autonomous mode
│   ├── vN-assumptions.md
│   ├── vN-repro.md
│   └── vN-ship-gate.md
├── audits/meta/
│   └── vN-meta-audit.md        # Meta-Auditor trajectory review every N versions (autonomous mode)
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

- Exit 0 is required. Errors block the gate.
- Warnings surface on the dashboard's Consistency panel (see `dashboard-spec.md`).
- **Rolling window of aligned knowledge:** every new finding, journal entry, and lesson is cross-checked against every prior claim; contradictions are flagged before they fork the narrative.

## Coverage map (Iron Law #25)

`coverage.json` is the compass for the exploration loop. See `templates/coverage.schema.json`.

- **Before picking an area:** query `coverage.json` for the highest-leverage unexplored or non-exhausted area.
- **After VALIDATE exit:** append approaches tried to `pattern_area.approaches_tried[]`; update `remaining_leverage_estimate`; set `ceiling_reason` when `exhausted: true`.
- **Brainstorm trigger:** required when entering an unexplored area, or when the chosen approach family is not already logged. Legacy per-phase brainstorms remain the default on v1.

## Autonomous mode

When `<project-root>/autonomous.yaml` is present (not inside ds-workspace/), `/ds`
bypasses the five framing questions and reads the file for framing answers, budget,
secondary metrics, and auto-pivot rules. Autonomous mode substitutes mechanical /
Council-based actors for human-gated decisions (see the "Autonomous mode layer"
section of `iron-laws.md`), but relaxes no iron law. Every substitution is declared
up-front in `autonomous.yaml.persona_substitutions` and audited at ship.

Core-law human gates that autonomous mode **does not** substitute:
- Any override of Iron Laws #1 (locked holdout), #12 (DGP memo signed), #16 (one-shot
  external submission), #17 (consistency alignment), #20 (eval-harness lock), or
  `law=budget` requires a `user` entry in `signed_by`. `scope=permanent` is additionally
  rejected outright for #16 and #20 (use scope=run with a re-lock plan).
- External submission (Iron Law #16) always halts the auto-ship ceremony before the
  external push — the human must execute the submit.
- User-initiated `reset-submission` or `reset-surrender` after an auto-defeat.

## Lessons compaction

`lessons.md` is append-only within a version but periodically compacted across versions per Iron Law #23 scaling guidance.

- **Cadence:** at `v{10, 50, 100, 500, 1000, ...}`.
- **Action:** dedupe, generalize, and promote durable lessons to `~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<slug>.md`.
- **Archive:** pre-compaction `lessons.md` is preserved as `lessons-vK.md.archive`.

## Retention

Orchestrator never auto-deletes. Runs may transition status (`valid` → `superseded` | `invalidated`) but stay on disk. User manually prunes.

## Promotion target

Generalizable lessons from `disproven/` or `findings/` are promoted (with Skeptic + Statistician sign-off) to:

```
~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<lesson-slug>.md
```
