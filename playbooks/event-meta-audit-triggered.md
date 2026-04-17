# Event: meta-audit-triggered

## Trigger
Any of the conditions in
[personas/meta-auditor.md](../personas/meta-auditor.md) §"When invoked":
1. `current_v - state.last_meta_audit_v >=
   autonomous.yaml.autonomy.require_meta_audit_every_n_versions` (default
   10).
2. Before emitting `disproven/surrender-vN.md` (Iron Law #22 auto-defeat).
3. When any scope=permanent override of a non-core iron law is created.
4. Before auto-ship in autonomous mode.
5. On-demand via `/ds meta-audit`.
6. Anti-thrash: three consecutive `auto-pivot` events cycling through the
   same 2 pattern areas.
7. Scope-creep: third active scope=permanent override across all laws.
8. Goodhart-drift: third `anti-goodhart-*` scope=run override for the same
   secondary within 5 versions.

## Immediate response (in order)
1. Append `meta-audit-triggered` to `state.events_history` with `ref`
   describing which trigger condition fired.
2. Dispatch Meta-Auditor subagent with the full Inputs list from the
   persona file. MUST be a fresh-context subagent (Task/Agent tool) — no
   inline persona invocation.
3. Do NOT proceed with the action that triggered the audit (ship, pivot,
   surrender, permanent override) until Meta-Auditor returns a verdict.
4. Await verdict:
   - **PASS** — action proceeds; `state.last_meta_audit_v = current_v`;
     Meta-Audit artifact committed.
   - **BLOCK** — action refused; proceed to §Block response.

## Required inputs to Meta-Auditor dispatch
- Path: the Meta-Auditor dispatch prompt.
- Must include: current vN, trigger condition, all file paths enumerated
  in [personas/meta-auditor.md](../personas/meta-auditor.md) §Inputs.
- Must NOT include: the orchestrator's current working hypothesis or
  "what I'm trying to do" framing — Meta-Auditor needs fresh context, not
  pre-conditioned priors.

## Block response
1. Record Meta-Auditor verdict + reasoning at
   `<meta_audit_dir>/vN-meta-audit.md` (the Meta-Auditor writes this directly).
   `<meta_audit_dir>` comes from `autonomous.yaml.logging.meta_audit_artifact_dir`
   (default `audits/meta/`).
2. Orchestrator writes `audits/vN-meta-audit-block-response.md`
   documenting:
   - Which trigger condition fired.
   - Which CRITICAL findings Meta-Auditor raised.
   - Chosen remediation (one of: fix underlying issue, re-tune thresholds,
     escalate to human, abort).
3. If remediation is threshold re-tuning or coverage re-seeding, author
   the corresponding Iron Law #24 override-card with `signed_by: [user]`
   (Council cannot re-tune the autonomous-mode contract — that requires
   human authorisation).
4. If remediation is "escalate to human", fire
   `escalate_to_human.meta_auditor_critical_finding`; set
   `state.autonomous = false`; halt autonomous loop.
5. After remediation, re-dispatch Meta-Auditor to confirm the issue is
   resolved. Only then does the originally-blocked action resume.

## Required artifacts
- `<meta_audit_dir>/vN-meta-audit.md` — Meta-Auditor's output, every run.
  `<meta_audit_dir>` is read from `autonomous.yaml.logging.meta_audit_artifact_dir`
  (default `audits/meta/`); the orchestrator MUST create the directory if it does
  not exist before dispatching the Meta-Auditor.
- `audits/vN-meta-audit-block-response.md` — orchestrator's response, block
  case only.
- Optional: `overrides/vN-override-autonomy-thresholds.md` if thresholds
  are re-tuned.

## Resolution criteria
- PASS: `state.last_meta_audit_v = current_v` AND the originally-deferred
  action proceeds.
- BLOCK: remediation artifact exists AND re-dispatched Meta-Auditor
  returns PASS AND `consistency_lint.py` exits 0.

## Anti-gaming
- `state.last_meta_audit_v` is strictly monotonic — the orchestrator
  cannot decrement it to delay a cadence-driven audit.
- If two consecutive cadences are missed (e.g., `current_v = 25`,
  `last_meta_audit_v = 10`, cadence = 10), the orchestrator must run TWO
  meta-audits before proceeding — audits are not batched.
- Meta-Audit artifacts are committed to the repo; their absence at ship
  is caught by `consistency_lint.py` and
  `scripts/verify_skill_files.py` in autonomous mode.

## Events this can chain into
- `escalate_to_human.meta_auditor_critical_finding` on persistent BLOCK.
- `override-activated` when remediation writes a threshold override.

## Interactive mode
Meta-Audit is advisory in interactive mode. `/ds meta-audit` still
dispatches and writes the artifact, but a BLOCK verdict does not refuse
actions — the user decides. Trigger condition #1 (cadence-driven) is
inactive in interactive mode unless explicitly requested.

## Resume phase
- **PASS:** the originally-deferred action proceeds — ship, pivot, surrender, or permanent override write. `state.current_phase` advances per that action.
- **BLOCK, remediated:** after the block-response artifact is written AND re-dispatched Meta-Auditor returns PASS, resume the originally-blocked action.
- **BLOCK, escalated:** `state.autonomous = false`; next `/ds` invocation resumes in interactive mode at `state.current_phase` with the meta-audit BLOCK artifact surfaced.
