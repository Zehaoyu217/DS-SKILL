# Checklist: Ship Gate

Two-stage gate. **Internal-ship** (always required) validates the model against the locked internal holdout. **External-submit** (competition mode, Iron Law #16) sends the one-shot prediction file. Every box ticked at each stage, or no ship.

## Stage 0: Pre-ship preconditions (run before Stage 1)

Each bullet tags the Iron Law it enforces. Paste the named section into
`audits/vN-ship-gate.md` so the ship-gate audit is a self-contained receipt.

- **#1 Holdout integrity** — `state.holdout_reads == 0`
  (`jq '.holdout_reads' ds-workspace/state.json`) AND
  `holdout/HOLDOUT_LOCK.txt` sha256 matches the data-contract entry.
- **#21 Budget** — `python3 scripts/budget_check.py ds-workspace --check`
  exits 0 OR every active `law=budget` override is re-authorised here;
  remaining envelope → §"Budget snapshot". No unresolved `budget-exceeded`
  event without a matching override-card or path-B journal entry.
- **#22 No pending auto-defeat** — `disproven/surrender-vN.md` absent for
  current vN AND `state.phase != ABORTED`.
- **#23 Anti-Goodhart** — every pre-registered secondary metric has a
  non-null value for the winner; none degraded beyond its
  `max_degradation_sigma` vs the feature-baseline. Per-metric value + σ-gap
  → §"Anti-Goodhart snapshot". Active `law=anti-goodhart-*` overrides
  re-listed under #24.
- **#24 Override re-authorisation** — enumerate every
  `state.active_overrides` row (`id | law | scope | expires_at |
  re-authorise?`) → §"Active overrides". `scope=run|version` either
  expired or marked for expiration (list `affected_runs`).
  `scope=permanent` re-authorised per mode. Permanent overrides of laws
  #1, #12, #17 or `law=budget` REQUIRE a fresh `user` signature even in
  autonomous mode. Laws #16 and #20 REJECT `scope=permanent` outright —
  a permanent-scope card for either is a hard lint failure (use
  `scope=run` + re-lock plan). `python3 scripts/consistency_lint.py
  ds-workspace` exits 0.
- **#25 Coverage** — `coverage.json` validates against
  `templates/coverage.schema.json`. Every `priority: top` area is
  `exhausted == true` with a `ceiling_reason` OR appears in the winner's
  `notes_ref` (unexplored top areas block competition-mode ship; warn in
  daily). Summary (`area | approaches_tried | exhausted | ceiling_reason`)
  → §"Coverage snapshot".

### Autonomous-mode-only (skip in interactive mode)
- [ ] `<meta_audit_dir>/vN-meta-audit.md` with `verdict: PASS`; cadence
  satisfied (`current_v - last_meta_audit_v <=` `autonomous.yaml` cadence).
  Default `<meta_audit_dir>` = `audits/meta/`.
- [ ] `audits/vN-council-ship.md` with ≥2/3 Skeptic variants PASS +
  Meta-Auditor PASS.
- [ ] No unresolved `escalate_to_human` event since the last ship.

---

## Stage 1: Internal-ship

### Blockers
- [ ] Zero open CRITICAL findings from Skeptic, Validation Auditor, Statistician, Engineer, Domain Expert.
- [ ] All HIGH findings resolved or explicitly waived in `audits/vN-ship-gate.md` with rationale.
- [ ] Narrative Audit ([narrative-audit.md](narrative-audit.md)) signed PASS (Iron Law #14).

### Pre-registration diff
- [ ] Every "Pre-registered decision" in `plans/v1.md` is compared against the final model/feature set.
- [ ] Any divergence is listed in `audits/vN-ship-gate.md` with rationale. Unexplained divergence = BLOCK.

### Metric
- [ ] CV metric meets pre-declared target (recorded in `plans/v1.md` framing, never moved).
- [ ] `cv_std` and `cv_ci95` present for the winning run.
- [ ] Multi-seed stability: ≥3 seeds run; seed-to-seed std reported and < 50% of lift-vs-baseline.
- [ ] Lift vs baseline is statistically significant (Statistician-signed).

### Expanded gap check
- [ ] `predicted_interval = cv_mean ± (2·cv_std + λ·max(0, adv_auc - 0.5) + μ·dup_ratio)` computed before holdout read (Iron Law #13).

### Internal holdout read (the only one)
- [ ] Read `ds-workspace/holdout/holdout.parquet` exactly once.
- [ ] Increment `state.holdout_reads` to 1 and stamp `audits/vN-repro.md`.
- [ ] If holdout metric is outside the expanded predicted interval → fire `cv-holdout-drift`, do NOT ship.

### Reproducibility
- [ ] Engineer re-ran random-fold within tolerance.
- [ ] `env.lock`, `seed.txt`, `data.sha256` committed.

### Artifacts
- [ ] `report.md` generated: framing, DGP memo summary, CV results, holdout result, disproven-cards list, promotion candidates.
- [ ] `report.pdf` optional.
- [ ] Dashboard `leaderboard.json` shows the winning run with `status: valid` and no other run with a higher metric.

### Personas
All five: Skeptic + Validation Auditor + Statistician + Engineer + Domain Expert. Every one signs `audits/vN-ship-gate.md`.
- [ ] Each persona audit has `automated: true` and `review_type: subagent | human` declared.
- [ ] For high-stakes ship gates (competition mode or user-flagged), consider requesting `review_type: human` on at least Skeptic and Domain Expert.
- [ ] In daily mode, only Skeptic + Validation Auditor sign-offs are blocking; others are advisory but still produced.

### Cross-persona debate
- [ ] Skeptic and Statistician conduct the structured debate defined in [templates/persona-debate.md](../templates/persona-debate.md) **after** independent sign-offs are collected.
- [ ] Debate artifact `audits/vN-debate-ship.md` has `verdict: consensus-pass`. An `unresolved-block` hard-blocks the ship gate regardless of mode.
- [ ] If HIGH residual caveats remain: they are listed in `audits/vN-ship-gate.md` with documented waivers signed by the orchestrator. CRITICAL caveats cannot be waived.

---

## Stage 2: External-submit (competition mode only)

Only runs after Stage 1 passes AND the user has declared competition mode in FRAME (or subsequently enabled it via `/ds submit`).

### Format
- [ ] Full [submission-format.md](submission-format.md) checklist PASS.
- [ ] `scripts/check_submission_format.py submissions/vN/submission.csv data/sample_submission.csv` exits 0.

### Provenance
- [ ] `submissions/vN/submission.sha256` present.
- [ ] `submissions/vN/provenance.json` records seed / env / data hash / winning-run id / timestamp / git commit.
- [ ] Engineer verified regen to byte-equality on at least a sampled subset.

### Final authorization
- [ ] User has typed `ship external` (or equivalent explicit confirmation) after seeing the internal-holdout metric and the predicted interval.
- [ ] Orchestrator prints a one-way banner: "SUBMITTING — this is a single-shot action. No further code changes will be permitted without `/ds reset-submission`."

### After submit
- [ ] State transitions to `submitted`.
- [ ] `submissions/vN/submitted.txt` written with timestamp and sha256.
- [ ] Final report committed.

Any check failure at Stage 2 fires `submission-drift`; remediate, re-sign full ship-gate, and re-run external-submit. The organizer submission counter is the user's responsibility — the skill will not override a user's explicit intent to retry.
