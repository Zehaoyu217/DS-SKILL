# Checklist: Narrative Audit

"Does the model tell a reasonable story?" Iron Law #14. Run before internal-ship. A model with high CV that tells an incoherent story is suspected of overfitting or leakage until proven otherwise.

## Inputs
- `runs/vN/metrics.json` (winning run)
- Top-K feature importances / SHAP values from the winning model (K=20 minimum)
- `audits/vN-model-diagnostics.md` (PDP, ICE, permutation importance, segment weakness analysis from Iron Law #18)
- `dgp-memo.md` §7 (pre-registered expected feature directions)
- `findings/` cards for this vN

## Checks

- [ ] **Direction check.** For each of the 3–5 features pre-registered in `dgp-memo.md` §7, the observed coefficient sign / SHAP direction matches the expected direction. Any mismatch is HIGH and requires a written explanation or a disproven-card against the prior.
- [ ] **Top-K coherence.** The top-5 features by importance have a plausible mechanistic link to the target. "Plausible" means: Domain Expert or Skeptic can name the mechanism in one sentence.
- [ ] **No suspicious IDs.** No top feature is a row identifier, a timestamp without seasonality rationale, a hash, a free-text id, or a near-constant column. Hits of this kind = BLOCK (Iron Law #14 violation).
- [ ] **Counterfactual spot-checks.** Pick 3 rows with high-confidence predictions. For each, perturb the top-1 feature by its IQR and verify the prediction moves in the direction the mechanism predicts. Record in `audits/vN-narrative.md`.
- [ ] **Suspicious-lift trigger.** If CV metric is > 3σ above the strongest baseline AND lift cannot be explained by a named mechanism in ≥2 sentences, fire `suspicious-lift` event.
- [ ] **Monotonicity where expected.** If the DGP memo predicts monotonic dependence on a feature, verify partial-dependence is monotonic (Spearman rank of PDP > 0.7 in the predicted direction). Non-monotonicity on a feature predicted to be monotonic = HIGH. Cross-reference with ICE plots from `audits/vN-model-diagnostics.md` — heterogeneous ICE curves around a monotonic PDP suggest subpopulation effects worth investigating.
- [ ] **Permutation importance cross-check.** Compare SHAP-based ranking against permutation importance ranking from `audits/vN-model-diagnostics.md`. Large discrepancies (>5 rank positions) for a top-10 feature require explanation (multicollinearity, interaction effects, or target leakage).
- [ ] **Segment weakness review.** Review flagged segments from `audits/vN-model-diagnostics.md` §2. Any segment where metric drops >1σ below overall AND represents >5% of data must have either: (a) a documented explanation, (b) targeted feature engineering attempted, or (c) explicit acknowledgment as a known limitation. Shipping a model with unexplained weakness on a material segment is HIGH.
- [ ] **Leakage-by-importance heuristic.** If a feature tagged `at-label` or `post-label` in the DGP provenance table appears in top-10 importance, BLOCK. The provenance audit should already have caught this, but this is the fallback.

## Persona output
Skeptic signs `audits/vN-narrative.md`:

```markdown
# Narrative Audit vN
Reviewer: Skeptic (with Domain Expert cross-reference)
Date: <ISO>
Top-K features reviewed: <list>
Direction matches: <x/y>
Mechanism sentence per top-5:
  1. <feature> — <one-sentence mechanism>
  ...
Counterfactual spot-checks: <3 rows, predicted-vs-perturbed delta>
Verdict: [PASS | BLOCK | SUSPICIOUS-LIFT]
Sign-off: yes/no
```

A BLOCK or SUSPICIOUS-LIFT verdict blocks SHIP and forces either (a) a remediation in v(N+1), or (b) a documented downgrade to a simpler model whose story the team can defend.
