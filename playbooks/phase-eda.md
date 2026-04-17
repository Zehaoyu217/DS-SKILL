# Phase: EDA

## Entry gate
DATA_PREP exited (`audits/vN-data-prep.md` signed by Engineer AND no new leakage patterns from Validation Auditor).

## Purpose
Creative pattern-finding without rigor gatekeeping. Explorer persona runs first to surface surprising patterns, correlations, and temporal dynamics. Goal: discover testable hypotheses backed by plots and intuition, before model fitting.

## Steps (in order)
1. Invoke Explorer persona to run univariate, bivariate, and temporal analysis. Explorer may use any visualization or statistical exploration tool.
2. Save all plots to `runs/vN/plots/` (organized by theme).
3. For each major finding, add at least one testable hypothesis with explicit kill criterion to `plans/vN.md` or (if this is an exploratory round) to `plans/v(N+1).md`.
4. Skeptic optionally reviews new hypotheses at phase exit (non-blocking, advisory only).
5. **Append plan-update revision.** Write a revision block to `plans/v{N}-updates.md` summarizing: which hypotheses were refined or added, which pre-registered decisions (if any) were revised, which triggering plot / pattern motivated each change. Use [templates/plan-updates-vN.md](../templates/plan-updates-vN.md). If EDA produced no plan-affecting findings, write an explicit "no-changes" revision with a one-line rationale — silence is not acceptable.

## Persona invocations
- **Explorer** (primary): Conduct EDA on the dataset. Produce plots, summary statistics, and narrative. Output: plots in `runs/vN/plots/` and notes to inform plan updates.
- **Skeptic** (optional, non-blocking): Review any new hypotheses for clarity and falsifiability.

## Exit gate
All of the following must hold (ALL AND):
- At least one hypothesis with explicit kill criterion recorded in `plans/vN.md` or `plans/v(N+1).md`
- `plans/v{N}-updates.md` has a revision block appended at this EDA milestone
- `runs/v{N}/learnings.md` has an EDA exit entry appended, citing at least one concrete plot or artifact as the observation
- `audits/v{N}-explorer.md` frontmatter has `hypothesis_count >= 1` and `plot_count >= 5` (linter warns `lint.explorer-count-low` otherwise)

## Events that can abort this phase
- `assumption-disproven` (rare in EDA but possible if data patterns contradict framing; update data-contract and open v(N+1))
