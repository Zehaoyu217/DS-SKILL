---
name: ds-init
description: Bootstrap a data-science-iteration workspace inside the current project folder.
---

# /ds-init

Initialize `ds-workspace/` in the current project root. Idempotent — safe to re-run; never overwrites existing files.

## What it does

1. Creates the directory tree from [workspace-layout.md](../workspace-layout.md):
   `plans/ findings/ disproven/ literature/ audits/ runs/ nb/ src/{data,features,models,evaluation}/ step-journal/ dashboard/ holdout/`.
2. Seeds dashboard files from `dashboard-template/`.
3. Seeds `lessons.md`, `step-journal/v1.md`, and `nb/v1_sandbox.ipynb` from `templates/`.
4. Writes initial `state.json` and `dashboard/data/leaderboard.json`.
5. Drops a `holdout/HOLDOUT_LOCK.txt` placeholder and an empty `data-contract.md`.
6. Starts the dashboard server in the background (skip with `--no-server`).

## Run

From inside the project folder containing your data and docs:

```
python3 $SKILL/scripts/init_workspace.py
```

(With the skill installed globally, `$SKILL = ~/.claude/skills/data-science-iteration`. With project-level install, `$SKILL = .claude/skills/data-science-iteration`.)

### Arguments (optional)
- `--project-root PATH` — target folder (default: cwd).
- `--no-server` — do not launch the dashboard server.
- `--force` — re-seed missing files even if `ds-workspace/` already exists.

## After init

The orchestrator must now:

1. Ask the five framing questions (one at a time; the fifth is competition mode).
2. Dispatch Literature Scout (Lite) in parallel with plan drafting.
3. Draft `plans/v1.md` from `templates/plan-vN.md` with the YAML pre-registration block filled in.
4. Run Skeptic + Validation Auditor gate on the draft.
5. Enter the DGP phase: produce a signed `dgp-memo.md` from `templates/dgp-memo.md`, including the §7a structured predictions block.
6. Enter the loop: see [loop-state-machine.md](../loop-state-machine.md).

At every FINDINGS / MERGE / SHIP gate, the orchestrator must run:

```
python3 $SKILL/scripts/consistency_lint.py ds-workspace
```

and require exit 0 before proceeding (Iron Law #17).
