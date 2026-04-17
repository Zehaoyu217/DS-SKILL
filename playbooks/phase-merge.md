# Phase: MERGE

## Entry gate
≥2 sibling branches exist as `plans/vN.a.md`, `plans/vN.b.md`, ... AND each has reached FINDINGS. All branches share the same `dgp-memo.md` and `audits/vN-cv-scheme.md` (branching does not change framing, only model/feature hypotheses).

## Purpose
When parallel sub-plans run, MERGE picks the winner deterministically, keeps the winner's code path, and emits disproven-cards for every feature/model/approach dropped. Iron Law #15. No silent dropping; no eyeballing.

## When to branch (FORK heuristic)
Orchestrator proposes FORK at DGP exit or EDA exit when any of the following holds:
- Literature scout memo identifies ≥2 competitive families (e.g., GBM vs TabNet vs linear-with-interactions).
- Two EDA-generated hypotheses have non-overlapping feature sets.
- User says "try these in parallel: X, Y, Z".

Each branch `vN.x` gets its own `plans/vN.x.md`, `runs/vN.x/`, and dashboard rows prefixed with the branch tag.

## Steps (in order)

1. **Freeze.** Mark all sibling branches' FINDINGS signed. No new runs in any branch during MERGE.
2. **Canonicalize metrics.** For each branch winner, compute on the same CV folds (seed-locked from FRAME). If a branch used a different CV split, re-score on the canonical split before comparing. Record in `audits/vN-merge-metrics.md`.
3. **Pick winner.** Winner = branch with highest canonical `cv_mean - 2·cv_std` (lower-bound on CI). Ties broken by simpler model (fewer parameters, fewer features, shorter code). Record choice in `audits/vN-merge.md`.
4. **Cherry-pick.** Any feature or code module from a losing branch that was independently better on ablation than its equivalent in the winner is eligible for cherry-pick. Cherry-pick requires: (a) re-run on winner's pipeline with and without, (b) CV improvement with CI not crossing 0, (c) no leakage regression.
5. **Emit disproven-cards.** For every hypothesis in every losing branch that did not survive: write `disproven/vN-dNNN.md` with metric achieved, reason for loss, and whether to retry in a future v with different framing.
6. **Prune.** Delete `src/`, `runs/`, and dashboard rows from losing branches. Keep `plans/vN.x.md` and `disproven/` cards as the historical record.
7. **Single thread.** Orchestrator state moves back to the main thread `vN` (losing `vN.x` suffix). Next phase is SHIP if criteria met, else NEXT_V.

## Persona invocations
- **Statistician** (primary): Canonicalize metrics, verify winner CI-lower-bound comparison is valid, sign `audits/vN-merge-metrics.md`.
- **Skeptic** (primary): Review every disproven-card for "did we kill this for the right reason?"; sign `audits/vN-merge.md`.
- **Engineer** (primary): Execute cherry-pick re-runs and prune. Verify dashboard reflects post-merge state.

## Exit gate
All of the following must hold (ALL AND):
- `audits/vN-merge.md` signed by Skeptic and Statistician
- Exactly one winner branch remains
- Every losing branch has emitted disproven-cards for all its hypotheses
- Dashboard shows only the surviving runs
- **Consistency lint GREEN** — `python $SKILL/scripts/consistency_lint.py ds-workspace` exits 0 (Iron Law #17)
- Lessons from surviving + killed branches appended to `lessons.md` with explicit `supersedes:` chains where relevant

## Mode differences

**Competition mode:** Consistency lint must exit 0 (blocking) at MERGE exit. No exceptions.

**Daily mode:** Consistency lint is **warning-only** at MERGE exit — lint errors surface on the dashboard Consistency panel but do not block the gate. Lint becomes blocking again at SHIP exit. Use daily-mode lint warnings to track debt before the final ceremony, not to block progress.

## Events that can abort this phase
- `leakage-found` in a branch during canonicalization → that branch is invalidated entirely, does not compete.
- `suspicious-lift` on the proposed winner → re-evaluate with Narrative Audit before declaring winner.
