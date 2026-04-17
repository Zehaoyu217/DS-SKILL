# Event: council-quorum-failed

## Trigger
A Council dispatch in autonomous mode fails to produce a ≥2/3 PASS
verdict:
- **Ship authorisation** — Council convened to auto-ship does not reach
  quorum.
- **Override authorisation** — Council convened to approve an Iron Law #24
  override does not reach quorum.
- **Core-law guard** — Council attempts to authorise an override of
  Iron Laws #1, #12, #16, #17, #20 or `law=budget` at any scope (all
  of these require `user` in `signed_by`), and the orchestrator rejects
  the Council-only `signed_by` list. Scope=`permanent` for #16 or #20
  is rejected outright by the linter regardless of signers.

See [playbooks/autonomous-mode.md](autonomous-mode.md) §"Council quorum
protocol" for the variants and quorum rule.

## Immediate response (in order)
1. Append `council-quorum-failed` to `state.events_history` with `ref:
   audits/vN-council-<purpose>.md`.
2. Commit the Council artifact regardless — the individual verdicts and
   reasons are part of the record even when quorum fails.
3. Do NOT retry Council immediately. A single failure is often
   informative (the variants agree that the action is unsafe); repeated
   auto-retries would mask a real disagreement.
4. Increment a per-purpose failure counter in memory (not persisted —
   resets each `/ds` session). If two failures for the same purpose
   occur within the session, fire
   `escalate_to_human.council_failed_to_reach_quorum_twice`.

## Remediation paths

### Path A — First failure, retry with remediation
1. Read the three Council verdicts in
   `audits/vN-council-<purpose>.md`. Identify the common concern across
   BLOCK / ESCALATE votes.
2. Address that concern with a concrete action:
   - **Skeptic-A (leakage-prior) BLOCK**: re-run
     `checklists/leakage-audit.md`; tighten the audit if it passed
     superficially.
   - **Skeptic-B (overfit-prior) BLOCK**: run additional seeds; check
     CV-to-holdout gap; run adversarial-validation.
   - **Skeptic-C (Goodhart-prior) BLOCK**: re-evaluate secondary
     metrics; possibly fire `anti-goodhart-failure`.
3. Commit the remediation artifact to the relevant audit file.
4. Re-dispatch Council. The three variants see the remediation artifact
   as part of their fresh-context inputs.

### Path B — Second failure, escalate
1. Do NOT re-dispatch Council a third time autonomously.
2. Write `audits/vN-council-escalation.md` summarising:
   - The two failed Council attempts and their verdict deltas.
   - The remediation(s) attempted between attempts.
   - The specific variant(s) that still BLOCK, with their reasoning.
   - The orchestrator's recommended path (proceed with user sign-off,
     abandon the proposed action, pivot, etc.).
3. Fire `escalate_to_human.council_failed_to_reach_quorum_twice`. Set
   `state.autonomous = false`.
4. Next `/ds` invocation resumes interactive mode with the escalation
   audit surfaced.

### Path C — Core-law guard rejection
- This is NOT a variant-disagreement failure. The Council may have
  unanimously PASSed a permanent override of Iron Law #1 / #12 / #17 /
  #20 / law=budget, but the orchestrator rejects it because those laws
  require `user` in `signed_by`.
- Fire `escalate_to_human.permanent_override_of_core_law`. Do not retry;
  Council cannot authorise this class of override.
- The Council's unanimous verdict is still preserved in
  `audits/vN-council-<purpose>.md` as advisory input for the human
  reviewer.

## Required artifacts
- `audits/vN-council-<purpose>.md` — original Council dispatch record
  with all three variants' verdicts + reasons.
- Path A: remediation artifact (depends on the concern).
- Path B: `audits/vN-council-escalation.md` + escalation event.
- Path C: `audits/vN-council-core-law-escalation.md` + escalation event.

## Resolution criteria
- Path A: second Council dispatch produces ≥2/3 PASS AND the originally-
  blocked action proceeds.
- Path B: orchestrator exits autonomous mode; user re-engages manually.
- Path C: human reviewer either authorises the permanent override (with
  their own `signed_by: [user]` entry) or redirects.

## Events this can chain into
- `meta-audit-triggered` — if the two Council failures spanned different
  purposes, that is trajectory-level (Council's calibration may be off).
- Escalation events (not enum entries): various
  `escalate_to_human` conditions.

## Anti-gaming
- The per-purpose failure counter is session-scoped, not persisted. This
  is intentional: a Council failure on ship auth at v10 should not
  auto-escalate the first override-auth failure at v15, which is a
  different decision.
- BUT: Meta-Auditor's trajectory review counts Council failures across
  the whole project; chronic Council failures are a trajectory-level
  concern even when no session exceeds the two-failure threshold.

## Interactive mode
Council quorum protocol is autonomous-only; in interactive mode, user
authorisation replaces Council, so this event does not fire.

## Resume phase
- **Path A (remediate + retry):** on second Council PASS, resume at the gate that dispatched the Council (e.g., SHIP stage 0 or the override-write step). `state.current_phase` unchanged.
- **Path B (escalate):** `state.autonomous = false`. Next `/ds` invocation resumes in interactive mode at `state.current_phase` with the escalation audit surfaced.
- **Path C (core-law rejection):** terminal for autonomous mode; `state.autonomous = false`; user must sign in `signed_by: [user]` to re-open the gate.
