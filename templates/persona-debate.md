---
# Machine-readable metadata (consumed by scripts/consistency_lint.py).
id: debate-v{N}-{gate}       # e.g., debate-v1-DGP, debate-v1-SHIP
version: {N}
gate: DGP | SHIP
participants: [skeptic, statistician]
round_count: 1               # increment if more than one exchange is required
verdict: pending | consensus-pass | unresolved-block
created_at: YYYY-MM-DDTHH:MM:SSZ
resolved_at: null            # timestamp when verdict is set
---

# Persona Debate v{N} — {gate}

> **Purpose:** A structured two-turn exchange between Skeptic and Statistician at high-stakes gates. Parallel-independent sign-offs cannot catch internal consistency errors between behavioral concerns (Skeptic) and quantitative claims (Statistician). This debate format forces both personas to engage with each other's position before a gate can close.
>
> **When used:** DGP exit (structural assumptions vs. quantitative predictions), SHIP internal (narrative audit vs. statistical validity). Other gates use parallel independent sign-offs only.
>
> **Output path:** `audits/v{N}-debate-{gate-lowercase}.md` (e.g., `audits/v1-debate-dgp.md`, `audits/v1-debate-ship.md`).

---

## Artifact under review

*(List the artifacts both personas have read before the debate opens.)*

- DGP gate: `dgp-memo.md` + `audits/v{N}-skeptic-dgp.md` + `audits/v{N}-auditor-dgp.md` + `audits/v{N}-domain-dgp.md`
- SHIP gate: `audits/v{N}-ship-gate.md` + `audits/v{N}-narrative.md` + `runs/v{N}/metrics.json` + holdout result (if already read)

---

## Round 1

### Skeptic's opening position

**Persona:** Skeptic (subagent) | **Signed:** pending | signed | **Timestamp:** `<ISO>`

1–3 concrete concerns. Each MUST cite a specific field, section, or metric.
Vague concerns ("I'm not sure about the framing") are rejected.

For each concern `S-01, S-02, S-03` (at least one required):
- **Claim challenged:** quote or reference the specific claim.
- **Challenge:** what is wrong or underspecified.
- **Stakes:** `critical` (blocks until resolved) | `high` (must be addressed with rationale) | `medium` (advisory).
- **Resolution criteria:** what would resolve this — a calculation, a reference, a documented waiver.

---

### Statistician's response

**Persona:** Statistician (subagent) | **Signed:** pending | signed | **Timestamp:** `<ISO>`

Respond to each Skeptic concern in turn. Either rebut with evidence, concede
and propose a fix, or escalate to Domain Expert / Validation Auditor.

For each `Response to S-NN`:
- **Position:** `rebut` | `concede` | `escalate-to-<persona>`.
- **Evidence / calculation:** metric, CI, plot, or reference.
- **Proposed resolution (if concede):** what changes, which artifact is updated.

---

## Consensus block

*(Written by the orchestrator after both personas have signed. Required for `verdict: consensus-pass`.)*

**Resolved concerns:**
- S-01: <one-line resolution — what was agreed, what (if anything) was updated in the artifact>
- S-02: ...

**Residual caveats accepted (HIGH, not CRITICAL):**
- <Concern id>: <one-line rationale for why this proceeds despite the concern>

**Gate may proceed.** Both personas agree the artifact meets the bar for this gate. Residual caveats are recorded in `audits/v{N}-ship-gate.md` (SHIP) or `dgp-memo.md` (DGP) as HIGH findings with documented waivers.

---

## Unresolved block

*(Written if consensus cannot be reached — `verdict: unresolved-block`. Gate is hard-blocked.)*

**Unresolved concern(s):**
- S-{id}: <what remains in dispute>
- **Blocking rationale:** <why this cannot be waived — what failure mode it prevents>
- **Resolution path:** <what the orchestrator must do to re-open the debate — update which artifact, run which check>

**Gate is blocked.** Artifact must be updated and debate re-opened (increment `round_count`). If two rounds fail to reach consensus on a CRITICAL concern, escalate to human review.

---

## Round 2 (if needed)

Append here if round 1 produced "re-open". Same structure as Round 1 but
scoped to the unresolved concern ids from Round 1 and the updated artifact.
Round count cap is 2 — a second failure to reach consensus on a CRITICAL
concern hard-blocks the gate and escalates to human review.

---

## Usage rules

1. **Debate is not optional at DGP exit and SHIP.** Parallel sign-offs happen first; the debate is an additional artifact, not a replacement for independent sign-offs.
2. **Concerns must be cite-specific.** Generalized skepticism without a citation is not a valid concern — the Skeptic persona instruction requires specificity.
3. **Statistician must engage, not deflect.** "I'm not a domain expert" is only acceptable for S-concerns about real-world mechanism, and only when explicitly escalating to Domain Expert.
4. **Consensus-pass does not mean no concerns.** HIGH residual caveats can proceed with documented waivers. CRITICAL concerns cannot be waived — they must be resolved or they produce `unresolved-block`.
5. **Round count cap: 2.** If two rounds do not resolve CRITICAL concerns, the gate is blocked and a human must intervene. This prevents infinite debate loops.
6. **Orchestrator writes the consensus or unresolved block.** Neither persona writes this section — the orchestrator synthesizes both positions. This prevents either persona from unilaterally declaring victory.
