# Playbook: Autonomous Mode

This playbook defines how the orchestrator runs unattended when
`<project-root>/autonomous.yaml` is present. It references and enforces the
layer at the bottom of [iron-laws.md](../iron-laws.md) §Autonomous mode layer.

**Non-negotiable:** Autonomous mode never relaxes an iron law. It substitutes
*mechanical or council-based actors* for human-gated steps. Every substitution
is declared in `autonomous.yaml`, logged as an Iron Law #24 override at FRAME
exit, and audited at ship.

---

## Activation

1. At `/ds` entry (or `/ds-init` bootstrap), orchestrator probes for
   `<project-root>/autonomous.yaml`. Presence is the switch; absence means
   interactive mode.
2. If present: validate against the structure in
   [templates/autonomous.yaml](../templates/autonomous.yaml). Any missing
   required field (framing, secondary_metrics, budget, autonomy,
   persona_substitutions, escalate_to_human) rejects the autonomous bootstrap
   with a message and falls back to interactive FRAME.
3. Set `state.autonomous = true`. Write an Iron Law #24 override-card per
   substitution declared in `autonomous.yaml.persona_substitutions`:
   - `overrides/v1-override-domain-expert.md` (scope=permanent, signed_by:
     [literature-scout, meta-auditor])
   - `overrides/v1-override-ship-authorization.md` (scope=permanent, signed_by:
     [council, meta-auditor])
   - `overrides/v1-override-override-authorization.md` (scope=permanent,
     signed_by: [council])
   Each links to the autonomous.yaml block that authorised the substitution.
4. Seed `plans/v1.md` pre-registration from `autonomous.yaml.framing` and
   `autonomous.yaml.secondary_metrics`; seed `budget.json` from
   `autonomous.yaml.budget`; seed `coverage.json` pattern_area priority order
   from `autonomous.yaml.autonomy.pivot_priority_order`.
5. Log activation to `step-journal/v1.md` with the autonomous-mode marker and
   the list of generated override-card ids.

## Per-response reading order (autonomous)

Same as [human-in-the-loop.md](human-in-the-loop.md) §"Reading order" plus:

0. Read `autonomous.yaml`. Re-load on every response — the user may edit it
   between runs to retune thresholds, and stale in-memory config is a silent
   drift source.
0a. Consult `state.events_history` for any unhandled escalate-to-human event
   (see §Escalation below). If one is present, DO NOT proceed autonomously —
   halt, surface the event, wait for human input.

## Persona substitutions

Declared in `autonomous.yaml.persona_substitutions` and enforced by
`consistency_lint.py` via the Iron Law #24 override artifacts.

### Domain Expert
- **Substitute:** Literature Scout (full mode) + Meta-Auditor sign-off.
- **Where invoked:** DGP memo §8 (Iron Law #12), FRAME step 3 domain-specific
  validation.
- **Output:** Full-mode literature memo explicitly addresses domain plausibility
  of each DGP §7 prediction; Meta-Auditor trajectory review signs off that the
  memo engaged with the DGP claims rather than producing generic literature
  summary.
- **Limitation:** Literature Scout cannot generate priors beyond what the
  literature describes; novel-domain projects may still require human
  escalation — surface via `escalate_to_human: meta_auditor_critical_finding`
  when Meta-Auditor marks literature coverage as `low confidence`.

### Ship authorisation
- **Substitute:** Council quorum (≥2 of 3 Skeptic variants) + Meta-Auditor.
- **Where invoked:** SHIP phase entry in place of user-typed `ship`.
- **Mechanics:** see §Council quorum below. Council dispatches
  Skeptic-variant-A, Skeptic-variant-B, Skeptic-variant-C (distinct priors
  declared in their dispatch prompts); a PASS verdict from ≥2 of 3 plus a PASS
  from Meta-Auditor permits auto-ship.
- **Fallback on quorum failure:** emit `council-quorum-failed` event and escalate
  per `escalate_to_human.council_failed_to_reach_quorum_twice`.

### Override authorisation
- **Substitute:** Council quorum (≥2 of 3 Skeptic variants).
- **Scope rules** (enforced by `consistency_lint.py`):
  - `scope=run|version` of non-core laws: Council-only OK.
  - `scope=permanent` of non-core laws: Council + Meta-Auditor.
  - Any scope of core laws #1, #12, #16, #17, #20 or `law=budget`:
    `signed_by` MUST include `user`. Council never substitutes.
    Orchestrator halts and escalates via
    `escalate_to_human.permanent_override_of_core_law`.
  - `scope=permanent` of laws #16 or #20: rejected outright (use
    `scope=run` + re-lock plan).

## Council quorum protocol

Council = three Skeptic subagents dispatched with deliberately different priors
so their verdicts are not trivially correlated. Priors:
- **Skeptic-variant-A — "assume leakage":** start from the hypothesis that
  leakage is present; require the evidence to falsify it.
- **Skeptic-variant-B — "assume overfit":** start from the hypothesis that the
  best model is overfit; require evidence of generalisation.
- **Skeptic-variant-C — "assume Goodhart":** start from the hypothesis that
  the primary metric is being gamed at the cost of the pre-registered
  secondaries; require secondary-metric trajectory evidence.

Each variant returns a PASS / BLOCK / ESCALATE verdict and a one-paragraph
reason. Quorum rule: ≥2 of 3 PASS = Council PASS. Any ESCALATE = auto-escalate
regardless of the other verdicts. Two consecutive Council failures fire
`council-quorum-failed` twice, triggering `escalate_to_human` per
`autonomous.yaml.escalate_to_human.council_failed_to_reach_quorum_twice`.

Artifacts:
- `audits/vN-council-<purpose>.md` lists each variant's verdict + reason + the
  prior prompt it was dispatched with.
- `state.events_history` appends `council-quorum-failed` event with `ref` to
  the artifact.

## Meta-Auditor cadence

Dispatched per [personas/meta-auditor.md](../personas/meta-auditor.md) at:
1. Every `autonomous.yaml.autonomy.require_meta_audit_every_n_versions`
   versions (default 10). Orchestrator consults `state.last_meta_audit_v`
   and dispatches when `current_v - last_meta_audit_v >= cadence`.
2. Before emitting `disproven/surrender-vN.md` (Iron Law #22 auto-defeat).
3. When any scope=permanent override of a non-core iron law is created.
4. Before auto-ship (when `ship_target` is met AND all gates PASS).
5. On-demand via `/ds meta-audit`.

On Meta-Auditor BLOCK: refuse auto-ship / surrender / permanent override.
Append `meta-audit-triggered` event and surface via
`escalate_to_human.meta_auditor_critical_finding`.

Anti-gaming: `state.last_meta_audit_v` is monotonic — never decreased. If a
cadence is missed (e.g., `current_v = 25`, `last_meta_audit_v = 10`, cadence
= 10), the orchestrator is required to run two Meta-Audits before proceeding
— audits cannot be batched or skipped.

## Iron Law #21 — budget monitoring

Every run calls `scripts/budget_check.py <ds-workspace> --account <run_id>
--vN <N> --cost compute_hours=<h>,api_cost_usd=<c>` after the run completes.
Exit code 3 = budget exceeded; orchestrator refuses further runs until either:
- An Iron Law #24 override (`law=budget`, `scope=run|version`) is authorised
  by Council (Council CANNOT authorise `scope=permanent` for law=budget —
  that always escalates via `escalate_to_human.budget_exhausted_before_ship`),
  OR
- Iron Law #22 auto-defeat fires.

Budget-exceeded event is idempotent: repeated calls at the same version with
the same exhausted dimensions are no-ops.

## Iron Law #22 — auto-pivot / auto-defeat

Autonomous-mode triggers are defined here; full trigger/response/artifact detail lives in the event playbooks.

- **Auto-pivot** — fires when `state.plateau_streak >= autonomous.yaml.autonomy.plateau_threshold` (default 3). See [event-auto-pivot.md](event-auto-pivot.md) for pivot selection, Explorer dispatch, anti-thrash guard.
- **Auto-defeat** — fires when all `coverage.json.pattern_areas[]` are exhausted, OR `sum(state.pattern_area_plateaus.values()) >= exhaustion_threshold` (default 6). See [event-auto-defeat.md](event-auto-defeat.md) for Meta-Auditor gate, surrender ceremony, reset protocol.

Interactive mode uses the same thresholds but writes proposal artifacts (`audits/vN-pivot-proposal.md` / `audits/vN-surrender-proposal.md`) and waits for the user.

## Iron Law #23 — anti-Goodhart monitoring

Every VALIDATE exit runs [checklists/anti-goodhart.md](../checklists/anti-goodhart.md) (Statistician). Secondary degrading >Nσ (threshold per `autonomous.yaml.secondary_metrics[].max_degradation_sigma`, default 2) while primary improved fires `anti-goodhart-failure`. See [event-anti-goodhart-failure.md](event-anti-goodhart-failure.md) for path A (reject) / path B (override) / path C (amend secondaries). Autonomous authorisation: Council-only for scope=run; Council + Meta-Auditor for scope=version (rarely appropriate).

## Iron Law #24 — override governance

All overrides in autonomous mode follow this filesystem shape:
- File: `overrides/vN-override-<law-slug>.md` using
  [templates/override-card.md](../templates/override-card.md).
- `signed_by` MUST be a YAML list. Scalar string rejected by
  `consistency_lint.py`.
- `scope=run`: expires at run completion (orchestrator clears from
  `state.active_overrides` after run's VALIDATE exit).
- `scope=version`: expires at vN rollover (orchestrator clears at MERGE or
  SHIP exit, whichever fires first).
- `scope=permanent`: NEVER expires automatically. Re-authorised at every SHIP
  gate (ship-gate checklist lists each active permanent override for
  explicit re-sign-off).
- `user_guidance_ref`: null in autonomous mode (no human G-NNN entry backs
  these). The `reason` field carries the full justification plus a pointer to
  the triggering event or artifact.

## Iron Law #25 — coverage-driven exploration

`coverage.json` is the authoritative ledger of explored pattern areas. On VALIDATE exit, orchestrator:
1. Appends the run's approach family to `pattern_areas[<area>].approaches_tried`.
2. Sets `last_tried_vN = current_v`.
3. Updates `remaining_leverage_estimate` from run outcome.
4. On exhaustion indicators (≥3 approaches with no lift, or intrinsic ceiling from diagnostics): writes `ceiling_reason ∈ {approach-exhausted, feature-limited, intrinsic}` and `exhausted = true`.
5. Increments `state.pattern_area_plateaus[<area>]`.
6. If `current_v - last_tried_vN >= 5` for any non-exhausted area, fires `coverage-stale` — see [event-coverage-stale.md](event-coverage-stale.md).

## Escalation

When any condition in `autonomous.yaml.escalate_to_human` fires:
1. Orchestrator halts the autonomous loop immediately (no new runs, no
   phase transitions).
2. Writes `audits/vN-escalation-<condition>.md` with: which condition fired,
   the triggering artifact, last 3 versions of leaderboard, current
   `state.json`, and Meta-Auditor's last verdict (if any).
3. Sets `state.autonomous = false` and appends an escalation event to
   `events_history`.
4. Next `/ds` invocation resumes in interactive mode with the escalation
   audit surfaced. Re-entering autonomous mode requires the user to explicitly
   clear the escalation (`clear-escalation` command) and, if the escalation
   was a Council failure, optionally retune Council priors in
   `autonomous.yaml`.

## Ship in autonomous mode

Auto-ship preconditions are enforced by
[checklists/ship-gate.md](../checklists/ship-gate.md); this section names
only the autonomous-specific additions (beyond every checklist item):

1. `state.phase == SHIP` AND `state.autonomous == true`.
2. Primary metric meets
   `autonomous.yaml.framing.success_threshold.target` (direction-aware).
3. `audits/vN-council-ship.md`: ≥2/3 Skeptic variants PASS.
4. `audits/meta/vN-meta-audit.md`: Meta-Auditor PASS.
5. No active escalate-to-human event in `events_history`.

On PASS: write `audits/vN-ship-gate.md` signed by `[council,
meta-auditor]`, perform the ship ceremony, stop. Authorising run id is
logged on the leaderboard `ship_authorized_by` field. On FAIL: pivot
(plateau_threshold hit) or escalate (CRITICAL gate failure).

### External submission is always human-gated

Iron Law #16 is NOT mechanically relaxable. Even with full Council +
Meta-Auditor PASS, autonomous mode MUST NOT push to an external system
(Kaggle, production registry, public leaderboard, or any endpoint visible
outside `ds-workspace/`). The auto-ship ceremony terminates at
`audits/vN-ship-gate.md` and stops; a human runs the external-submit step.
`consistency_lint.py` `LAWS_REJECT_PERMANENT` rejects any `scope=permanent`
override of #16 regardless of signers.

## Audit trail (logged at SHIP)

The ship-gate audit re-lists every declared substitution, every override
generated at activation, every Council event, every Meta-Auditor verdict,
and every escalation — the filesystem-visible record that the loop stayed
inside its declared boundaries.
