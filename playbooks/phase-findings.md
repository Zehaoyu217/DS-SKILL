# Phase: FINDINGS

## Entry gate
VALIDATE exited (Statistician signed off, uncertainty metrics present, assumptions tested).

## Purpose
Resolve every hypothesis from the plan. Each hypothesis receives a determination: confirmed (finding-card) or disproven (disproven-card). Promotion vote on disproven cards. Final Skeptic review. Propose next iteration or open ship gate.

## Steps (in order)
1. For each hypothesis id listed in `plans/vN.md`, decide confirmed or disproven based on CV results and analysis.
2. For confirmed hypotheses, write `findings/vN-fNNN.md` using the finding-card template. For disproven, write `disproven/vN-dNNN.md` using the disproven-card template.
3. Run promotion vote on each disproven-card: Skeptic and Statistician each vote yes/no. If both vote yes, mark for promotion to `~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<lesson-slug>.md`.
4. Skeptic performs final review of all findings and disproven cards. Output: `audits/vN-findings-review.md` with Verdict [PASS | BLOCK].
5. Orchestrator proposes: (a) `ship` if stop criteria are met (metrics pass, no blockers), OR (b) opens `plans/v(N+1).md` with refined hypotheses if iteration should continue.

## Persona invocations
- **Skeptic** (primary): Review all hypothesis determinations, promotion votes, and card quality. Output: `audits/vN-findings-review.md` with Verdict.
- **Statistician** (parallel, promotion votes): Vote on disproven-card promotion to ds-learnings.

## Exit gate
Every hypothesis id from `plans/vN.md` resolved to exactly one artifact (`findings/vN-fNNN.md` or `disproven/vN-dNNN.md`). Skeptic Verdict=PASS in `audits/vN-findings-review.md`.

## Events that can abort this phase
- `assumption-disproven` (finding disproves a core framing assumption; update data-contract and open v(N+1))
- `metric-plateau` (two consecutive vN show no stat-sig improvement; trigger full Literature Scout memo for v(N+1))
- `cv-holdout-drift` (at ship gate, gap exceeds predicted interval; do NOT ship; open v(N+1) investigating drift source)
