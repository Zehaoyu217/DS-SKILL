---
kind: override
id: vN-override-<law-slug>
law: <law-name-or-number>              # e.g. 'eval-harness', 'budget', 'anti-goodhart-shrink', '19b-feature-baseline'
scope: run                              # run | version | permanent
vN: <integer>
created_at: <ISO-8601>
expires_at: <ISO-8601 | null>           # null allowed only for scope=permanent
signed_by:                              # MUST be a YAML list, not a scalar. Council quorum >=2 for scope=permanent.
                                        # Permitted signer values: user | council | meta-auditor | <Skeptic-variant-A>
                                        # Core-law overrides (#1,#12,#16,#17,#20) AND law=budget REQUIRE one 'user' entry at any scope, even in autonomous mode. Laws #16,#20 REJECT scope=permanent outright — use scope=run with a re-lock plan.
  - <user | council | meta-auditor>
council_signatures:                     # required when scope=permanent in autonomous mode
  - reviewer: Skeptic-variant-A
    verdict: PASS
  - reviewer: Skeptic-variant-B
    verdict: PASS
  - reviewer: Meta-Auditor
    verdict: PASS
expected_risk: "<CRITICAL | HIGH | MEDIUM | LOW — what could go wrong>"
mitigation: "<what we are doing instead to contain the risk>"
reason: "<why relaxing this law is justified here>"
affected_runs: []                       # run ids invalidated or re-scored under this override
reverts_at: "<phase | event | null>"    # when does this stop applying
user_guidance_ref: <G-NNN | null>       # USER_GUIDANCE.md entry that authorised this (null if council-initiated)
agent_pushback_given: true | false      # did the orchestrator raise the concern before accepting the override?
agent_pushback_text: "<quoted — empty string if none>"
---

# Override: <law>

## Context

What triggered this override (link the artifact or event id that forced the decision).

## Why this law cannot be followed as-written

Concrete constraint that makes literal compliance impossible or wasteful. Be specific — "project constraint" is not a reason.

## What we are doing instead

Exact compensating procedure. Must be at least as testable as the law being relaxed.

## Risk and monitoring

- Risk surface opened by this relaxation:
- Monitoring added to detect if the risk materializes:
- Automatic revert trigger (what event causes this override to be retracted):

## Audit trail

- [ ] Override artifact filed in `overrides/`
- [ ] `state.active_overrides` updated with this id
- [ ] Referenced in `audits/vN-ship-gate.md` at SHIP for re-authorization (scope=permanent only)
- [ ] Consistency linter recognizes the artifact as present
- [ ] `signed_by` is a YAML list with >=1 entry (>=2 for scope=permanent); includes `user` for core-law permanent overrides

## Post-SHIP review

Filled in after ship:
- Did the risk materialize? yes/no, with evidence.
- Should this override be promoted to a durable Iron-Laws amendment, left as a scoped exception, or rescinded?
