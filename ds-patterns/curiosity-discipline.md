# Curiosity Discipline Patterns

Patterns for keeping the exploration loop from settling into laziness.
Pull this up when multiple versions have passed without a Research Lead
coach note, when the primary metric moves by <0.001 per version for
several versions, when `coverage.json` shows one pattern area
monopolising attempts, or when the orchestrator has been running model
variants without the knowledge base moving.

These patterns sit alongside Iron Laws #22 (plateau / auto-pivot), #25
(coverage-driven exploration), and #26 (model-as-teacher). The iron laws
enforce hard gates; these patterns supply the soft discipline that keeps
the iron laws from being the only pressure.

---

## Direction Fatigue Counter

**Worth exploring when:** The same pattern area has accumulated ≥3
attempts in `coverage.json` with outcome ∈ {neutral, regressed} and
|lift| < 0.001, OR the same model family has been tried in ≥k
consecutive versions without a material lift.

**What to try:** Maintain `direction_fatigue_counter` per pattern area
in `coverage.json` (schema v2). Increment on each attempt with |lift| <
`direction_fatigue_threshold` (default 0.001). Reset on a material lift
or a confirmed disproven-card. When the counter reaches
`direction_fatigue_threshold` (default 4), the orchestrator MUST dispatch
the Research Lead before opening the next version. The coach note
names ≥2 alternate pattern areas with concrete first-step experiments.

**Ceiling signal:** Fatigue counter stays below threshold across all
active pattern areas for 3+ versions — exploration is diversified.

**Watch out for:** The plateau counter in Iron Law #22 is global and
coarse — 3 consecutive plateaus fires auto-pivot regardless of where
they happened. The fatigue counter is per-area and finer — it catches
the case where one area eats all the attempts while other areas never
get tried. Both should be active; they catch different failure modes.
A project can run 6 consecutive model-family tuning rounds with
Δ ≈ 0.0002 each — Iron Law #22 never fires (each is weakly positive)
but a per-area fatigue counter does.

---

## Variable Exploration Rotation

**Worth exploring when:** `knowledge-base.md` §2 has variables with
`explored: []` and `in_feature_basis: true`, OR a Research Lead coach
note lists in-basis unexplored variables, OR the last 3 versions have
all been model-family-tuning attempts.

**What to try:** Pick one unexplored in-basis variable per version
(round-robin). Produce at minimum: a univariate histogram, a permutation
importance estimate, and either a PDP or a segment split. Write the
result into §2 as an `explored` entry with kind and finding_ref. Do this
as a *sidecar* to whatever modeling run the version was already going to
do — not as a replacement.

**Ceiling signal:** Every in-basis variable has ≥1 `explored` entry and
a `last_reviewed` stamp within the last 5 versions.

**Watch out for:** The instinct is to skip sidecar exploration when the
modeling run is busy; that is exactly how the "never revisits feature
selection" trap happens. Treat the sidecar as a 10-minute task with a
one-line KB patch — cheap relative to the run it accompanies. If the
sidecar surprises you (an "uninteresting" variable has real segment
signal), it becomes a §6 implication in the synthesis.

---

## Weakest-Segment Focus

**Worth exploring when:** `knowledge-base.md` §6 shows a segment with
`trend_last_k_versions: flat` or `regressing` for ≥3 versions, OR
`ds-session-digest.sh` surfaces `kb.segment-flat` or
`kb.segment-regressing`, OR model-synthesis §4 has flagged the same
weakest segment across 3 consecutive versions.

**What to try:** Allocate one full version to the weakest segment.
Possible moves: a segment-specialist model trained on only the segment's
rows, a per-segment SHAP pruning to find features the global model
under-weights in that segment, a non-linear blend routing predictions
by segment membership, or a pure data-understanding round to find
variables that differentiate inside the segment. Do not return to
whole-population modeling until the segment has either moved or been
confirmed at intrinsic ceiling.

**Ceiling signal:** The segment has improved by ≥σ in 2 consecutive
segment-focused versions, OR 3 segment-focused versions have returned
neutral with different approaches (approach-exhausted for this
segment).

**Watch out for:** Segment specialists can catastrophically fail when
the segment is small and the specialist over-fits — training a
specialist on a 10%-of-population segment can produce worse segment
metric than the global model. A reliable segment move usually comes
from features or blend-level routing, not from architectural
specialisation.

---

## Coach-Note Cadence

**Worth exploring when:** More than 5 versions have elapsed since the
last `audits/vN-research-lead.md`, OR the orchestrator has not proposed
a pivot in a plateau window, OR autonomous mode has been running with
no Research Lead invocation.

**What to try:** Commit to a coach-note cadence: at every FINDINGS
exit plus at any `direction_fatigue_threshold` hit plus at any
`ds-stale-basis-check.sh` hook fire. Use `/ds-coach` in interactive
mode, or an autonomous dispatch in autonomous mode. Treat the coach
note as a first-class input to the next version's plan — at least one
proposed direction in `plans/v(N+1).md` must trace back to the coach
note.

**Ceiling signal:** Every plan's `plans/vN.md` either cites a coach
note as a direction source or explicitly records "coach note
considered, alternative chosen because X".

**Watch out for:** A coach note that is produced but ignored is
ceremony. The value comes from the orchestrator actually using one of
the coach's ranked directions — even if the orchestrator rejects the
top-ranked, the rejection reason belongs in the plan. Good example:
a user provides a handful of explicit redirections and the orchestrator
opens a multi-version plan that traces each redirection to a specific
phase. If the orchestrator cannot cite the coach as a direction source
in the next plan, the note was ignored.

---

## Multi-Metric Learning (Not Just Primary)

**Worth exploring when:** The last 3 model-synthesis artifacts all
filled §1 with primary+overfit_delta and left §4 (segments) / §5
(disagreement) sparse, OR the Research Lead has flagged "single-metric
trap" in a recent coach note.

**What to try:** At VALIDATE exit, require the synthesis to populate
at least 4 of the 5 §§1-5 sections with real content. Any section
marked "N/A" needs a reason sentence. Specifically: §4 (segment
weakness) and §5 (model disagreement) are the ones most commonly
under-filled. If the run produces no blend OOFs, §5 can be "no blend
this version" with a forward-looking note.

**Ceiling signal:** 3 consecutive syntheses have all 5 metric sections
filled with concrete content; no section has been "N/A" without a
reason.

**Watch out for:** Step-journals often report the primary metric and
overfit_delta for every run while almost never reporting segment-
metric *trends across versions*, even though those are computed per
run. The metric is *produced*, not *used* as a learning input. The
discipline is to use the metric in a forward-looking way: every
synthesis §4 answers "did we move the weakest segment?" — not just
"what did the segments score?".

---

## When to Accept a Ceiling

**Worth exploring when:** Multiple pattern areas have `exhausted: true`
in `coverage.json` with `ceiling_reason ∈ {approach-exhausted,
feature-limited, intrinsic}`, the plateau counter has approached
`plateau_threshold × 2`, and the Research Lead coach note says "no
obvious next direction with high confidence".

**What to try:** Accept the ceiling and emit a surrender-card
(template: `disproven/surrender-vN.md`). The card records the ceiling
evidence and the pattern areas attempted. In competition mode, submit
the current best. In daily mode, consider whether the project's framing
is worth re-opening (new data sources, different target definition,
different success criterion).

**Ceiling signal:** Surrender-card is accepted by Meta-Auditor and by
the user; `state.phase = ABORTED`.

**Watch out for:** Accepting a ceiling too early is as expensive as
pushing through a real ceiling too late. The discriminator is: does
the coach note name a plausible direction? If yes and the direction
has not been tried, try it. If the direction is vague ("more
regularization", "try another model family") or has been tried under a
different label, the ceiling is real. Good ceiling-acceptance looks
like: after a plateau window, the pause note itemises the evidence
(versions attempted, disproven-cards produced) and gives the user a
concise menu of options to pick from — not a vague "we are stuck".
