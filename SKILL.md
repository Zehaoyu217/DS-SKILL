---
name: data-science-iteration
description: Use when working from a dataset or model-with-data goal; runs a suspicious-yet-creative iterative loop (v1 → v2 → …) with gated phases, persona sign-offs, a signed DGP memo, locked-holdout discipline, adversarial validation, parallel-branch merge, narrative audit, and one-shot submission discipline. Two modes — competition (full ceremony, one-shot submission) and daily (lighter gates, faster iteration). Built for messy data where fooling yourself is the failure mode.
---

# Data Science Iteration

## The Iron Law

```
NO PHASE TRANSITION WITHOUT A SIGNED GATE.
NO MODELED RUN OFF THE DASHBOARD.
THE DGP MEMO IS SIGNED BEFORE ANY MODELING.
THE INTERNAL HOLDOUT IS READ EXACTLY ONCE AT INTERNAL-SHIP.          [competition mode]
THE EXTERNAL SUBMISSION IS SENT EXACTLY ONCE AT EXTERNAL-SUBMIT.     [competition mode]
```

See [iron-laws.md](iron-laws.md) for the full 19-law list and enforcement mechanics.

## Modes

This skill operates in one of two modes, chosen at FRAME (framing question 1e):

### Competition mode (full ceremony)
For Kaggle-style one-shot competitions, high-stakes research modeling, and any project where a wrong answer is worse than a slow answer. All 19 iron laws enforced. Internal holdout locked. External submission is one-shot. All persona gates are blocking. Full sign-off ceremony at every phase transition.

### Daily mode (lighter gates, faster iteration)
For general data science work — exploration, internal analyses, recurring model refreshes, prototyping. Key differences:

| Aspect | Competition | Daily |
|---|---|---|
| Holdout lock | Locked before modeling, read exactly once at ship | Holdout carved but may be evaluated more than once (logged) |
| External submission | One-shot, sha256-logged, irreversible | N/A |
| Persona sign-offs | All blocking at every gate | Skeptic + Auditor blocking; others advisory |
| DGP memo | Full §1–§8, 3 sign-offs required | §1–§4 + §7a required; §5–§6 optional; Skeptic sign-off required, others advisory |
| Literature Scout | Lite memo mandatory at FRAME; Full on novel/plateau | Optional (recommended on novel/plateau) |
| Ship gate | 5-persona ceremony + narrative audit + expanded gap | Skeptic + Auditor sign-off + narrative audit |
| Parallel branches | Full MERGE ceremony with disproven-cards | Lightweight comparison; disproven-cards still required |
| Consistency lint | Blocking at FINDINGS/MERGE/SHIP | Blocking at SHIP only; warning at FINDINGS/MERGE |

**All other iron laws apply in both modes.** The DGP memo, adversarial validation, data prep, leakage audit, disproven-cards, uncertainty reporting, baseline-first (model AND feature), brainstorm-before-build, and narrative audit are never skipped — they are the core discipline. Daily mode reduces ceremony, not rigor.

## Orchestration anchor (read every response, before anything else)

At the start of every response, before consulting `lessons.md`, `iron-laws.md`, or any
prior finding:

1. **Read `ds-workspace/USER_GUIDANCE.md`** — load the `## Current focus` header
   (phase, verbosity, active_overrides) and all `active` G-NNN entries.
   The most recent active entry reflects the user's current intent and is the primary
   anchor for all decisions this response.

2. **Follow `playbooks/human-in-the-loop.md`** for:
   - **Knowledge-lint** — before citing prior knowledge to push back on a user proposal
   - **Decision narration** — before each non-trivial action (checkpoint block)
   - **Override handling** — when user guidance conflicts with a rule or finding

This does not weaken any iron law. It governs *when and how* the orchestrator communicates
and responds. Gates are still mechanical; personas still dispatch as independent subagents.

## When to Use

- Starting a modeling project from data or a loose goal.
- One-shot Kaggle-style competitions with a hidden test set (→ competition mode).
- General data science work: exploration, analysis, recurring model builds (→ daily mode).
- When discipline matters more than speed (research, high-stakes decisions, reproducible science).
- When the decision/metric is roughly known. If it isn't, brainstorm the framing first, then enter this skill.

## When NOT to Use

- Production MLOps, deploy, drift monitoring.
- AutoML bandits.
- Pure engineering tasks that happen to touch data.

## Entry flow

1. **Bootstrap** — run `/ds-init` (or `python3 $SKILL/scripts/init_workspace.py`) from the project root. This creates `ds-workspace/` per [workspace-layout.md](workspace-layout.md), seeds the dashboard from `dashboard-template/`, seeds `lessons.md` / `step-journal/v1.md` / `nb/v1_sandbox.ipynb` from `templates/`, writes `state.json` + initial `leaderboard.json`, and starts `server/serve_dashboard.py`.
2. Ask five framing questions, one at a time (the fifth is mode selection: competition or daily).
3. Dispatch Literature Scout (Lite) in parallel with plan drafting (competition mode required; daily mode recommended).
4. Draft `plans/v1.md` from `templates/plan-vN.md` with the YAML `pre_registration` and `hypotheses:` blocks filled in.
5. Run Skeptic + Validation Auditor gate on the draft.
6. Enter DGP phase. Produce signed `dgp-memo.md` with §7a structured predictions (template: [templates/dgp-memo.md](templates/dgp-memo.md)).
7. Enter loop: see [loop-state-machine.md](loop-state-machine.md).

Every FINDINGS / MERGE / SHIP gate runs `scripts/consistency_lint.py` — exit 0 required (Iron Law #17). In daily mode, consistency lint is blocking at SHIP only; warnings at FINDINGS/MERGE.

## Loop (summary)

Phases per vN: `FRAME → DGP → AUDIT → DATA_PREP → EDA → FEATURE_MODEL → VALIDATE → FINDINGS → (MERGE? → SHIP | NEXT_V)`.

Branches `vN.a / vN.b / vN.c` can run in parallel between DGP and FINDINGS; MERGE picks the winner and emits disproven-cards for losers. See [playbooks/phase-merge.md](playbooks/phase-merge.md).

SHIP has two stages in competition mode: **internal-ship** (locked internal holdout, exactly one read) then **external-submit** (organizer's hidden test, exactly one submission).

Events (`leakage-found`, `assumption-disproven`, `metric-plateau`, `cv-holdout-drift`, `covariate-shift`, `suspicious-lift`, `submission-drift`, `novel-modeling-flag`, `novel-feature-flag`) can abort mid-phase.

## Personas and who gates what

See [personas/](personas/). Quick map:

| Gate | Competition mode | Daily mode |
|---|---|---|
| FRAME exit | Skeptic + Validation Auditor + Literature Scout (Lite memo present) | Skeptic + Validation Auditor (Lite memo recommended) |
| DGP exit | Skeptic + Validation Auditor + Domain Expert (independent) + Skeptic×Statistician debate (`audits/vN-debate-dgp.md` consensus-pass) | Skeptic + Auditor advisory + Skeptic×Statistician debate (same requirement) |
| AUDIT exit | Validation Auditor (leakage + adversarial validation) | Validation Auditor (leakage + adversarial validation) |
| DATA_PREP exit | Engineer (data prep audit signed) + Explorer advisory brainstorm + data_baseline.txt + brainstorm-DATA_PREP with ≥3 alternatives per >5%-missing col + plan-updates revision | Same |
| EDA exit | ≥1 hypothesis with kill criterion + plan-updates revision appended | Same |
| FEATURE_MODEL entry | model baseline + feature baseline (Iron Law #19) + Explorer advisory brainstorm + brainstorm-FEATURE_MODEL Skeptic-signed + brainstorm-FEATURE_ENG + (if tuning) brainstorm-TUNING + tuning-plan.md Skeptic-signed §4 + default-params run on leaderboard + literature Full memo if novel-modeling-flag or novel-feature-flag + adversarial audit present | Same (Literature Full memo optional on novel flags; Skeptic micro-audit still required) |
| VALIDATE exit | Statistician (uncertainty + multi-seed stability) + Validation Auditor | Statistician (uncertainty + multi-seed stability) |
| FINDINGS exit | every hypothesis resolved to finding-card or disproven-card + consistency lint GREEN | every hypothesis resolved + consistency lint warning-only |
| MERGE exit | Skeptic + Statistician + Engineer + consistency lint GREEN | Skeptic + consistency lint warning-only |
| SHIP (internal) | Skeptic + Auditor + Statistician + Engineer + Domain Expert (independent) + Skeptic×Statistician debate (`audits/vN-debate-ship.md` consensus-pass) + narrative-audit PASS | Skeptic + Auditor (independent) + Skeptic×Statistician debate (same requirement) + narrative-audit PASS + consistency lint GREEN |
| SHIP (external) | internal-ship passed + submission format valid + sha256 logged + user re-confirm | N/A |

## Persona dispatch via subagents

**Every persona invocation MUST run as an independent Claude Code subagent** (via the `Task` tool / `Agent` tool). This provides genuine independence — a subagent auditing work cannot see the orchestrator's chain-of-thought that produced it. The orchestrator dispatches persona subagents and collects their audit artifacts at each gate.

### Dispatch pattern

```
Orchestrator (main agent)
├── Task: "Skeptic audit of plans/v1.md" → returns audits/vN-skeptic.md
├── Task: "Validation Auditor leakage sweep on src/" → returns audits/vN-leakage.md
├── Task: "Domain Expert review of dgp-memo.md" → returns audits/vN-domain-dgp.md
└── Task: "Literature Scout Lite for problem class X" → returns literature/vN-memo.md
```

Each subagent receives:
1. The persona definition file (e.g., `personas/skeptic.md`)
2. The relevant checklist(s) (e.g., `checklists/leakage-audit.md`)
3. The artifact(s) to audit (e.g., `plans/v1.md`, `dgp-memo.md`, `src/`)
4. The current `state.json` and mode (competition/daily)

Each subagent returns:
1. Its audit file written to the expected path
2. A verdict: PASS, BLOCK, or ADVISORY (daily mode only for non-required personas)

### Parallel dispatch

Use parallel subagents for:
- **Parallel plans**: `vN.a / vN.b / vN.c` branches each run to FINDINGS before MERGE (Iron Law #15).
- **Parallel persona audits** at heavy gates: Skeptic + Validation Auditor + Domain Expert at DGP exit; Skeptic + Statistician at FINDINGS; all five at SHIP.
- **Explorer dispatch for brainstorms** (Iron Law #19): Explorer runs at DATA_PREP entry and FEATURE_MODEL entry *as an independent subagent* that does NOT see the orchestrator's preferred approach, so its creative candidates genuinely expand the option set rather than ratify a pre-chosen answer.
- **Skeptic micro-audits on brainstorms**: at FEATURE_MODEL entry, Skeptic is dispatched against the model-family brainstorm with `request-rework` authority — narrow or poorly-justified option sets are sent back before modeling begins.
- **Domain Expert synthesis** when no human expert is present: subagent cross-references DGP memo against literature and data dictionary; audit records `synthetic: true`.

### Why subagents, not inline personas

An inline persona (the same LLM writing the plan and then "auditing" it) provides zero independence. A subagent starts with a fresh context, sees only the artifact and the persona instructions, and has no access to the orchestrator's reasoning. This is closer to genuine peer review. It also allows parallel dispatch — multiple personas audit simultaneously rather than sequentially.

## Dashboard contract

Every modeled run must appear in `ds-workspace/dashboard/data/leaderboard.json` before its phase can exit. Invalidated runs (leakage, suspicious-lift, shift-pending) stay visible but render muted. See [dashboard-spec.md](dashboard-spec.md).

## Rolling knowledge loop (v3)

Iteration happens inside a **rolling window of aligned knowledge**, not an append-only archive. Every artifact carries a machine-readable claim block and the orchestrator cross-checks them every gate:

- **Structured claims:** finding-cards, disproven-cards, plan hypotheses, and DGP §7a predictions all have YAML frontmatter with `id`, `subject`, `direction`, `supersedes`, `superseded_by`, `status`, etc. (see `templates/*.md`).
- **Step journal:** `ds-workspace/step-journal/vN.md` is an append-only chain-of-thought log — each non-trivial decision records reasoning, alternatives, and which findings/predictions/hypotheses it touches.
- **Rolling lessons:** `ds-workspace/lessons.md` consolidates promoted findings and disproven across all versions with explicit `supersedes` chains; never edit history, only append new entries that retract old ones.
- **Sandbox notebook:** each version gets `nb/vN_sandbox.ipynb` seeded from `templates/sandbox-vN.ipynb` with a strict probe format (Context → COT → Code → Output → Interpretation → Link-out to finding/journal).
- **Consistency lint:** `scripts/consistency_lint.py ds-workspace` runs at FINDINGS exit, MERGE exit, and SHIP entry (Iron Law #17). It flags unresolved hypotheses, orphan DGP predictions, opposite-direction live claims on the same subject, broken supersedes chains, silent primary-metric drift across versions, and leaderboard top-runs that no finding claims.

Net effect: the agent is **always informed, always aligned, always corrected** — new claims cannot quietly contradict prior claims and stale claims cannot linger.

## Brainstorm-before-build and progressive planning (Iron Law #19)

The skill's anti-laziness discipline extends beyond "did you run the diagnostics?" to "did you consider enough options?" Two coupled artifacts enforce genuine exploration:

### Brainstorm files (`runs/v{N}/brainstorm-v{N}-<PHASE>.md`)

At the entry of DATA_PREP and FEATURE_MODEL (and at the sub-step of tuning when tuning is performed), the orchestrator writes a brainstorm file using [templates/brainstorm-vN.md](templates/brainstorm-vN.md). Required content: ≥3 candidate approaches with pros, cons, feasibility, and literature / memo references; a picked approach with rationale; rejected alternatives with one-line reasons; and a concrete contingency.

- **DATA_PREP** produces `brainstorm-v{N}-DATA_PREP.md` — per-column handling strategies for any column with >5% missing; domain-specific cleaning ideas seeded by Explorer.
- **FEATURE_MODEL** produces three brainstorms: `brainstorm-v{N}-FEATURE_MODEL.md` (model families, Skeptic micro-audit required), `brainstorm-v{N}-FEATURE_ENG.md` (feature representations), and — if tuning is performed — `brainstorm-v{N}-TUNING.md` (hyperparameters, search strategy, default-params baseline).

Explorer persona is dispatched as a subagent at DATA_PREP entry and FEATURE_MODEL entry to seed the brainstorm with unusual / domain-specific candidates *before* the orchestrator's preferred approach is fixed. This is how the skill pushes creativity without sacrificing rigor: creative options go through the same gated ceremony as the obvious ones.

### Feature baseline (companion to model baseline)

Iron Law #5 mandates a model baseline before complex models. Iron Law #19(b) mandates a **feature baseline** — a run tagged `feature_baseline: true` using raw (un-engineered) features against the model baseline. Every engineered-feature candidate reports `feature_lift_vs_feature_baseline` separately from `lift_vs_baseline`, so feature-engineering lift is distinguishable from model-family lift. If tuning is performed, the same discipline applies at the parameter level: a `default_params` reference run is logged first, and tuned runs report `tuning_lift_vs_default`.

### Progressive planning (`plans/v{N}-updates.md`)

The plan written at FRAME is never rewritten in place. Every plan change — a hypothesis refined after EDA, a pre-registered decision revised after DATA_PREP surprise, a candidate dropped at FEATURE_MODEL — is appended as a dated revision block in `plans/v{N}-updates.md` using [templates/plan-updates-vN.md](templates/plan-updates-vN.md). Each revision cites the concrete triggering artifact ("`runs/v{N}/plots/feature-Y-distribution.png` showed bimodality, so H-v{N}-02 was refined to test each mode separately").

Revisions are appended at DATA_PREP exit, EDA exit, FEATURE_MODEL exit, and VALIDATE exit (where the log is closed with a summary block that seeds the next iteration's FRAME). The consistency linter warns on vN with fewer than 3 revisions — silent plans are either perfect (rare) or dishonest (common). The point of the progressive plan is to preserve the thinking trail so readers (and future Claude sessions) can see how the plan actually evolved in response to learning.

## Model diagnostics (Iron Law #18)

After FEATURE_MODEL and before VALIDATE, the orchestrator runs the **model diagnostics checklist** ([checklists/model-diagnostics.md](checklists/model-diagnostics.md)). This goes beyond "which model scored higher" to understanding *how* and *where* the model works and fails:

1. **Interpretability toolkit** — SHAP values (global + local), partial dependence plots (PDP), individual conditional expectation (ICE) plots, and permutation importance. These complement each other: SHAP shows contribution per prediction, PDP/ICE show marginal effects, permutation importance shows feature necessity.

2. **Segment-level weakness analysis** — For each important continuous feature, bin into quantiles and compute validation metric per bin. For each important categorical feature, compute validation metric per category. Flag segments where metric drops significantly (>1σ below overall). These weak segments are candidates for: targeted feature engineering, confounding variable investigation, or segment-specific models. Write findings to `audits/vN-model-diagnostics.md`.

3. **Learning from the model** — The model is an information source, not just a score. Diagnostics answer: Where does the model struggle? Which subpopulations are underserved? Are there interaction effects the DGP memo predicted that the model confirms or contradicts? Do the PDP shapes match the DGP §7a expected directions? Non-monotonic PDP on a feature predicted to be monotonic is a HIGH finding.

See [checklists/model-diagnostics.md](checklists/model-diagnostics.md) for the full checklist and [playbooks/phase-feature-model.md](playbooks/phase-feature-model.md) step 5 for integration into the loop.

## User commands during loop

- `status` — print current phase, blockers, leaderboard top-3.
- `ship` — open internal-ship sequence.
- `ship external` — open external-submit sequence (competition mode only).
- `abort` — tear down; dashboard preserved.
- `force v+1 <reason>` — close vN early and open v(N+1).
- `dig <hypothesis>` — branch investigation without leaving current vN.
- `fork <branch-names>` — create parallel sub-plans `vN.a / vN.b / ...`.
- `merge` — enter MERGE phase explicitly.
- `reset-submission` — roll back the `submitted` state to allow changes (user must give rationale).
- `brainstorm [topic]` — open collaborative brainstorm session at any phase; see `playbooks/collab-brainstorm.md`.
- `override <rule> [scope]` — explicitly override a rule (iron law # or lesson id); scope inferred from phrasing if omitted.
- `verbosity <quiet|normal|verbose>` — set decision narration level; updates `USER_GUIDANCE.md` header. Default: `normal`.
- `guidance` — print current `USER_GUIDANCE.md` active entries and current focus header.
- `why` — agent explains its last decision with full chain-of-thought, regardless of current verbosity setting.

## Red Flags (stop and check)

| Thought | Reality |
|---|---|
| "Let me just peek at the holdout" | Iron Law #1. Any unlogged read invalidates the run. |
| "CV scheme is obvious, skip the audit" | Iron Law #2. Time/group/stratified choice is signed before features. |
| "DGP memo is overhead" | Iron Law #12. Grep catches code leakage; the memo catches structural leakage. |
| "Literature review wastes time on this problem" | Iron Law #7. Lite memo at every FRAME. Full memo on novel or plateau. |
| "Train and test are the same distribution" | Iron Law #13. Measure it with adversarial validation before asserting it. |
| "Fit the scaler on all data for convenience" | Iron Law #3. Fit inside folds only. |
| "Point estimate is fine" | Iron Law #4. CI, CV-std, and seed-std required. |
| "Baseline is boring, go straight to GBM" | Iron Law #5. Baseline first, always. |
| "This hypothesis didn't pan out, move on" | Iron Law #6. Write the disproven-card. |
| "I can't explain why this feature works — but it does" | Iron Law #14. Narrative audit blocks ship. |
| "These two plans are close, pick either" | Iron Law #15. MERGE picks deterministically and emits disproven-cards for losers. |
| "Just resubmit, we have time" | Iron Law #16. External-submit is one-shot. |
| "t-test, run it" | Iron Law #8. Assumption tests first. |
| "Works on my machine" | Iron Law #9. Seed + env + data hash logged. |
| "Quick fit in the notebook cell" | Iron Law #10. Notebooks call `src/` only. |
| "Didn't log that run" | Iron Law #11. Not on dashboard = doesn't exist. |
| "First reasonable approach, skip the brainstorm" | Iron Law #19a. ≥3 alternatives or the phase doesn't exit. |
| "This feature is just a custom aggregation, no need for lit review" | Iron Law #7 + novel-feature-flag. If the representation is outside the standard set, the Full memo is required — "it's just an aggregation" is exactly the rationalisation that hides p-hacking. |
| "Engineered features beat raw, call it a win" | Iron Law #19b. Feature-baseline row required; `feature_lift_vs_feature_baseline` reported separately. |
| "Tuned params beat defaults, ship it" | Iron Law #19b. Default-params reference run required; `tuning_lift_vs_default` reported separately. |
| "Plan didn't change, skip the update log" | Iron Law #19 / #17. Either write a revision block with rationale or write an explicit "no-changes" revision — silence is treated as dishonest. |

## Experiment tracking integration

The built-in dashboard (`leaderboard.json` + live HTML) is the primary tracking system. Optionally, runs can also be logged to an external experiment tracker for team visibility and long-term persistence.

Supported integrations (configured in `state.json` field `tracker`):
- `"tracker": "mlflow"` — logs metrics, params, and artifacts to a local or remote MLflow server. Set `MLFLOW_TRACKING_URI` in env.
- `"tracker": "wandb"` — logs metrics, params, and artifacts to Weights & Biases. Set `WANDB_API_KEY` and `WANDB_PROJECT` in env.
- `"tracker": null` (default) — dashboard-only, no external logging.

When a tracker is configured, `scripts/tracker_log.py` handles both dashboard and tracker writes in a single call. The dashboard is always updated first; tracker failure (exit 2) does NOT block the pipeline. The dashboard remains the source of truth for gate decisions; the external tracker is a mirror.

```bash
# The orchestrator calls this at FEATURE_MODEL step 6 and at SHIP
python $SKILL/scripts/tracker_log.py ds-workspace runs/vN
```

See [checklists/experiment-tracking.md](checklists/experiment-tracking.md) for full setup and integration details.

## Hook setup (optional but recommended)

Two shell hooks in `scripts/hooks/` anchor the orchestrator's attention and guard against silent phase drift.

### `ds-state-surface.sh` — UserPromptSubmit

Surfaces current phase, version, mode, holdout-read count, and the last 8 lines of the step-journal on **every user message**, so the orchestrator never needs to re-read state files to know where it is.

### `ds-phase-check.sh` — Stop

Before Claude Code stops, checks whether the current phase's **primary exit-gate artifact** exists. Prints a human-readable warning if the gate is unsatisfied. Always exits 0 (advisory, never blocks stopping).

### Installation

Add the following to `~/.claude/settings.json` (substitute your actual `$SKILL` path for the path to this skill directory):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "command": "bash /path/to/skill/scripts/hooks/ds-state-surface.sh",
        "description": "Surface ds-workspace phase + last journal entry"
      }
    ],
    "Stop": [
      {
        "command": "bash /path/to/skill/scripts/hooks/ds-phase-check.sh",
        "description": "Warn if current phase exit gate is not satisfied"
      }
    ]
  }
}
```

### Security boundary

Both hooks are **read-only**. They parse `state.json`, `leaderboard.json`, and `step-journal.md` and print to stdout. They do not write or modify any file. The Stop hook always exits 0 to avoid blocking Claude Code from stopping. No credentials or secrets are read.

## Compatibility (optional)

This skill is standalone. It is compatible with but does not require: `superpowers:brainstorming`, `python-patterns`, `python-testing`, `eval-harness`, `exa-search`, `deep-research`, `continuous-learning`, `superpowers:dispatching-parallel-agents`.
