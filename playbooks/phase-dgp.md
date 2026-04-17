# Phase: DGP

## Entry gate
FRAME exited (`plans/vN.md` drafted, `data-contract.md` written, `audits/vN-cv-scheme.md` signed, holdout locked) AND Literature Scout Lite memo `literature/vN-memo.md` present.

## Purpose
Force an explicit answer to "what is the true data generating process?" before any EDA or modeling. The DGP memo names structural leakage risks that grep cannot see, the selection mechanism behind the training sample, and the distribution-shift axes between train and the organizer's hidden test. Skeptic + Validation Auditor + Domain Expert sign. Iron Law #12.

## Steps (in order)
1. Draft `dgp-memo.md` vN from `templates/dgp-memo.md`, filling every section. Do not leave sections blank; mark "unknown — see H-vN-xx" instead, and add a hypothesis to `plans/vN.md` that resolves the unknown.
2. For every feature in the provenance table, tag capture-time relative to the label event: `pre-label`, `at-label`, `post-label`. Any `at-label` or `post-label` field either drops out of the feature set or gets a written justification citing the source system.
3. Name the selection mechanism explicitly. If train and hidden test are drawn from different populations/times, list the expected shift axes (§5 of template).
4. Write §7 (story check) with 3–5 pre-registered expected feature directions. This is what the Narrative Audit will later compare against.
5. Dispatch Skeptic, Validation Auditor, and Domain Expert in parallel for independent sign-offs. Any CRITICAL finding blocks DGP exit and either rewrites the memo or opens v(N+1).

5b. **Cross-persona debate.** After the three independent audits are collected, dispatch Skeptic and Statistician as paired subagents to conduct the structured debate defined in [templates/persona-debate.md](../templates/persona-debate.md). The debate focuses on the internal consistency between behavioral concerns (Skeptic on §3/§4) and the quantitative claims in §5 and §7a (Statistician on shift magnitudes and expected effect sizes). Output: `audits/vN-debate-dgp.md`. Verdict must be `consensus-pass` before the gate closes. A `consensus-pass` with HIGH residual caveats is acceptable — record the caveats in the memo. An `unresolved-block` keeps the gate closed.

## Persona invocations
- **Skeptic** (parallel, independent): Adversarial read of §3 (selection) and §4 (confounds). Output: `audits/vN-skeptic-dgp.md`.
- **Validation Auditor** (parallel, independent): Cross-check §2 provenance against `data-contract.md` and sample rows. Any `at-label`/`post-label` field without justification is CRITICAL. Output: `audits/vN-auditor-dgp.md`.
- **Domain Expert** (parallel, independent; may be waived with written rationale if no expert available, recorded in memo): Cross-reference §1, §4, §6 against real-world mechanism knowledge. Output: `audits/vN-domain-dgp.md`.
- **Skeptic + Statistician** (paired, sequential debate after independents): Conduct the structured two-turn exchange defined in [templates/persona-debate.md](../templates/persona-debate.md). Output: `audits/vN-debate-dgp.md`.

## Exit gate
`dgp-memo.md` has three sign-offs (Skeptic, Validation Auditor, Domain Expert — or recorded waiver for Domain Expert) AND zero open CRITICAL findings across the three audits AND `audits/vN-debate-dgp.md` has `verdict: consensus-pass`.

## Mode differences

**Competition mode:** All three sign-offs (Skeptic, Validation Auditor, Domain Expert) are blocking. The `audits/vN-debate-dgp.md` `verdict: consensus-pass` is also blocking. No exceptions.

**Daily mode:** Skeptic sign-off is **blocking**. Validation Auditor and Domain Expert sign-offs are **advisory** — their audits are still dispatched and their findings are recorded in the memo, but an `advisory` sign-off (or documented waiver for Domain Expert) satisfies the gate. The debate (`audits/vN-debate-dgp.md`) is still required but an `unresolved-block` verdict triggers a warn rather than blocking the gate if both debating personas are run in advisory mode.

## Events that can abort this phase
- `assumption-disproven` (Domain Expert or Skeptic shows a framing assumption is structurally false → update `data-contract.md` and open v(N+1))
- `leakage-found` (structural leakage identified in provenance table → drop field or re-plan in v(N+1))
