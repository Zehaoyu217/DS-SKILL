# Workspace Layout (`ds-workspace/`)

Per-project, created at run start in the current project root. Never auto-pruned.

```
<project-root>/ds-workspace/
├── state.json                  # see templates/state.schema.json
├── data-contract.md
├── holdout/
│   ├── HOLDOUT_LOCK.txt        # sha256 + lock timestamp + DO NOT READ notice
│   └── holdout.parquet
├── plans/vN.md
├── findings/vN-fNNN.md
├── disproven/vN-dNNN.md        # first-class learning artifacts
├── literature/vN-memo.md
├── audits/
│   ├── vN-skeptic.md
│   ├── vN-leakage.md
│   ├── vN-cv-scheme.md
│   ├── vN-assumptions.md
│   ├── vN-repro.md
│   └── vN-ship-gate.md
├── runs/vN/
│   ├── metrics.json            # CV mean/std, CI, lift_vs_baseline, baseline flag
│   ├── env.lock
│   ├── seed.txt
│   ├── data.sha256
│   └── plots/
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
5. Start server via `$SKILL/server/serve_dashboard.py` pointing at `ds-workspace/dashboard/`.

## Retention

Orchestrator never auto-deletes. Runs may transition status (`valid` → `superseded` | `invalidated`) but stay on disk. User manually prunes.

## Promotion target

Generalizable lessons from `disproven/` or `findings/` are promoted (with Skeptic + Statistician sign-off) to:

```
~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<lesson-slug>.md
```
