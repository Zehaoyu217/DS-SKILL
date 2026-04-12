# Phase: EDA

## Entry gate
AUDIT exited (`audits/vN-leakage.md` Verdict=PASS).

## Purpose
Creative pattern-finding without rigor gatekeeping. Explorer persona runs first to surface surprising patterns, correlations, and temporal dynamics. Goal: discover testable hypotheses backed by plots and intuition, before model fitting.

## Steps (in order)
1. Invoke Explorer persona to run univariate, bivariate, and temporal analysis. Explorer may use any visualization or statistical exploration tool.
2. Save all plots to `runs/vN/plots/` (organized by theme).
3. For each major finding, add at least one testable hypothesis with explicit kill criterion to `plans/vN.md` or (if this is an exploratory round) to `plans/v(N+1).md`.
4. Skeptic optionally reviews new hypotheses at phase exit (non-blocking, advisory only).

## Persona invocations
- **Explorer** (primary): Conduct EDA on the dataset. Produce plots, summary statistics, and narrative. Output: plots in `runs/vN/plots/` and notes to inform plan updates.
- **Skeptic** (optional, non-blocking): Review any new hypotheses for clarity and falsifiability.

## Exit gate
At least one hypothesis with explicit kill criterion recorded in the plan (either `plans/vN.md` or `plans/v(N+1).md`).

## Events that can abort this phase
- `assumption-disproven` (rare in EDA but possible if data patterns contradict framing; update data-contract and open v(N+1))
