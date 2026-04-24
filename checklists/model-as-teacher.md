# Model-as-Teacher Gate Checklist

Produces and validates `audits/vN-model-synthesis.md` (template:
[templates/model-synthesis.md](../templates/model-synthesis.md)).

Required at VALIDATE exit. Competition mode: blocking. Daily mode:
warning.

## Mandatory sections

- [ ] **§1 Metric delta table.** Primary row present. Every segment
      declared in `knowledge-base.md §6` present. Flag column filled for
      every row.
- [ ] **§2 SHAP / importance delta.** Either top-K deltas filled OR an
      explicit "model has no feature importance" note with reason.
- [ ] **§3 PDP observations.** At least top-5 features by current
      importance scanned. Surprise column filled for every row.
- [ ] **§4 Segment weakness scan.** Every KB §6 segment present.
      Weakest-segment-improved question answered.
- [ ] **§5 Model disagreement signals.** Either residual-corr table filled
      OR explicit "no blend this version" note.
- [ ] **§6 Implications.** At least 1 bullet with a concrete KB-section
      target. Empty §6 fails the gate.
- [ ] **§7 Proposed KB patches.** Zero or more patches, one line each,
      correctly formatted.

## Quality bars

_Checked by orchestrator; Skeptic micro-review required in competition
mode when §6 updates a DGP hypothesis._

- [ ] Each §6 implication names a concrete variable, hypothesis, basis
      row, insight, or segment — not a generic claim.
- [ ] No section marked "N/A" without an explicit reason sentence.
- [ ] Weakest-segment trend is called out, even if overall metric
      improved. The single-metric trap is exactly the case where §4 is
      "everything fine" while one segment has been flat for 5 versions.
- [ ] If nothing is flagged in §1–§5, §6 still contains a positive
      statement of what was learned (e.g. "we confirmed prior insight
      MI-03 holds under new HP regime"). "Nothing new" with no
      explanation fails the gate.
- [ ] §7 patches are consistent with §6 implications — every §6 bullet
      targeting a KB section either produces a §7 patch or explains why
      no patch is needed yet.

## Failure modes to recognise

- **Copy-paste of diagnostics.** §2 should contain *changes vs previous
  champion*, not absolute values. If the table looks like
  `audits/vN-model-diagnostics.md §Importance`, the synthesis has been
  skipped.
- **Generic implications.** "Consider more feature engineering", "try
  more seeds", "experiment with ensemble weighting" are not valid §6
  bullets. Every implication names an object.
- **Segment amnesia.** §4 rows marked "up" while the same segment was
  "flat" for 3 prior versions indicate the synthesis is reading only this
  version. Cross-check against `knowledge-base.md §6` trend column before
  signing off.
- **Phantom lift.** A flagged-primary with no flagged-segment and no
  SHAP/PDP changes usually means seed variance, not learning.
  Double-check `seed_std` in `runs/vN/metrics.json` before claiming a
  persistent insight.

## Daily vs competition mode

| Condition | Competition | Daily |
|---|---|---|
| `audits/vN-model-synthesis.md` missing | BLOCK VALIDATE exit | WARN on dashboard |
| §6 empty or filled with generic bullets | BLOCK VALIDATE exit | WARN on dashboard |
| §7 inconsistent with §6 | BLOCK VALIDATE exit | WARN on dashboard |
| Skeptic micro-review absent when §6 updates a DGP hypothesis | BLOCK | optional |
| Any other mandatory box unchecked | BLOCK | WARN |

## Relationship to other artifacts

- **`audits/vN-model-diagnostics.md`** (Iron Law #18) — raw artifacts
  (SHAP values, PDPs, permutation importance). The synthesis reads these
  and distills deltas; it does not duplicate them.
- **`audits/vN-research-lead.md`** — the Research Lead reads the
  synthesis at FINDINGS exit and proposes cross-version direction. The
  synthesis is per-version; the coach note is cross-version.
- **`knowledge-base.md`** — §7 proposed patches feed here. Applied by
  the orchestrator via `/ds-kb apply-patches
  audits/vN-model-synthesis.md`.
- **`coverage.json`** — the orchestrator updates
  `pattern_areas[].approaches_tried` at VALIDATE exit. The synthesis's
  §6 implications inform what `remaining_leverage_estimate` should be
  adjusted to.
