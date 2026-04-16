# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is the **data-science-iteration** Claude Code skill — a self-contained package that installs into `~/.claude/skills/` and enforces disciplined, gated data-science loops. The working directory *is* the skill itself. Changes here affect how the skill behaves when invoked from any project.

## Commands

```bash
# Python tests (pytest)
python3 -m pytest tests/ -q

# Single Python test file
python3 -m pytest tests/test_schemas.py -q

# Dashboard JS tests (vitest)
cd tests/dashboard && npx vitest run

# Skill self-check (verifies all required files exist)
python3 scripts/verify_skill_files.py

# Consistency linter smoke test (needs a workspace to lint)
python3 scripts/consistency_lint.py ds-workspace

# Leakage grep (used by Validation Auditor during AUDIT phase)
bash scripts/leakage_grep.sh <src-dir>
```

## Architecture

### Skill entry points

The skill is invoked by two slash commands defined in `slash/`:
- `slash/ds-init.md` — bootstraps `ds-workspace/` in the user's project
- `slash/ds.md` — starts or resumes the loop

`SKILL.md` is the primary frontmatter + orchestration doc that Claude reads when the skill activates.

### Phase flow and gate enforcement

Phases: `FRAME → DGP → AUDIT → DATA_PREP → EDA → FEATURE_MODEL → VALIDATE → FINDINGS → MERGE? → SHIP`

Gate logic lives in:
- `loop-state-machine.md` — authoritative phase-entry gate table, events, stop criteria
- `iron-laws.md` — 19 laws each with a concrete file-system enforcement mechanism (no file = gate refused)
- `playbooks/phase-*.md` — step-by-step orchestrator instructions per phase
- `playbooks/event-*.md` — abort-event handlers (`leakage-found`, `covariate-shift`, `suspicious-lift`, `submission-drift`, `metric-plateau`, etc.)

### Personas (always run as independent subagents)

`personas/` defines 7 independent Claude subagents: Skeptic, Validation Auditor, Statistician, Engineer, Domain Expert, Explorer, Literature Scout. **Each persona must be dispatched via the `Task`/`Agent` tool with fresh context** — inline personas share the orchestrator's chain-of-thought and provide no independence. See `SKILL.md` § "Persona dispatch via subagents".

### Checklists

`checklists/` contains machine-readable gate checklists that personas fill in. Key ones:
- `leakage-audit.md` + `encoding-audit.md` — grep-based leakage patterns
- `adversarial-validation.md` — train-vs-test AUC check
- `ship-gate.md` — final ship ceremony (5-persona, narrative audit, predicted interval)
- `model-diagnostics.md` — SHAP/PDP/ICE/segment analysis (Iron Law #18)
- `narrative-audit.md` — model story vs DGP predictions (Iron Law #14)

### Scripts

`scripts/` — all called by the orchestrator at specific phase gates:
| Script | When called |
|---|---|
| `init_workspace.py` | `/ds-init` bootstrap |
| `consistency_lint.py` | FINDINGS/MERGE/SHIP gates (exit 0 required) |
| `adversarial_validation.py` | AUDIT phase |
| `check_submission_format.py` | External-submit gate (competition mode) |
| `tracker_log.py` | FEATURE_MODEL step 6 + SHIP (logs to leaderboard + optional MLflow/W&B) |
| `leakage_grep.sh` | AUDIT phase, called by Validation Auditor |
| `verify_skill_files.py` | Developer self-check |

### Templates

`templates/` — canonical templates that orchestrator copies into `ds-workspace/` at init or phase entry:
- `plan-vN.md` — structured plan with YAML `pre_registration` and `hypotheses:` blocks
- `plan-updates-vN.md` — progressive plan log (append-only revisions, never rewrite)
- `brainstorm-vN.md` — ≥3 candidate approaches framework (Iron Law #19a)
- `dgp-memo.md` — data-generating process memo, signed before any modeling
- `state.schema.json` + `leaderboard.schema.json` — JSON schemas validated by tests

### Dashboard

`dashboard-template/` — static HTML/CSS/JS dashboard seeded into `ds-workspace/dashboard/` at init. `server/serve_dashboard.py` serves it on a free local port (writes PID + URL to files for clean teardown).

Dashboard JS tests are in `tests/dashboard/` (vitest, ESM). Python tests are in `tests/` (pytest). Schema fixture tests are in `tests/test_schemas.py`.

### Modes

Competition mode (full ceremony, one-shot external submission) vs Daily mode (lighter gates, faster iteration). Mode is chosen at FRAME phase. The key invariants that **never change between modes**: DGP memo, adversarial validation, leakage audit, brainstorm-before-build, feature baseline, disproven-cards, model diagnostics, narrative audit.

## Key invariants when editing this skill

- **Gate enforcement is mechanical**: a gate is a file that must exist and be signed. If you add a new gate requirement, add the file-system check to `loop-state-machine.md` and the iron law to `iron-laws.md`.
- **`consistency_lint.py` is the source of truth** for cross-artifact claim alignment. If you add new structured-claim fields to templates, update the linter.
- **Templates are frozen contracts**: `state.schema.json` and `leaderboard.schema.json` are tested in `tests/test_schemas.py` against fixtures in `tests/fixtures/`. Schema changes require fixture updates.
- **Persona files are dispatch briefs, not inline prompts**: they tell the subagent what to look for and what to write; they don't contain the orchestrator's reasoning.

## data-science-iteration: Adding Lessons

When extracting lessons from a data science project (via claudeception or
manually), append findings to the relevant pattern file in `ds-patterns/`.
Follow the schema: update the **Watch out for** section of the most relevant
pattern with what was learned. Do not change the four-field pattern schema
(Worth exploring when / What to try / Ceiling signal / Watch out for) without
reviewing all existing pattern files for consistency.
