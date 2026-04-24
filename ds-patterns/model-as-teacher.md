# Model-as-Teacher Patterns

Patterns for treating a trained model as a *source of insight* about the
dataset, not just a score generator. Pull this up at VALIDATE phase (when
Iron Law #26 requires a synthesis), when SHAP/PDP/permutation artifacts
have been produced by Iron Law #18 but no persistent learning has been
extracted, or when the orchestrator is iterating on models without the
knowledge base moving.

The artifact these patterns feed is
`audits/vN-model-synthesis.md` — the mandatory distillation artifact.

---

## SHAP Delta Over SHAP Absolute

**Worth exploring when:** A new model champion has been identified, or
the feature basis has changed, or you are about to copy SHAP numbers from
`audits/vN-model-diagnostics.md` into the synthesis.

**What to try:** Record top-20 SHAP *changes* vs the previous champion,
not absolute values. For each of: ranks moved up ≥5, ranks moved down
≥5, new entrants in top-20, dropouts. Tag each change as expected
(known regularization / HP / feature-basis effect) or surprising. Put
surprises in `model-synthesis.md` §6 as implications — they are the
ones that update the knowledge base.

**Ceiling signal:** Top-20 SHAP is stable across the last 3 champions
(no features moving ≥5 ranks) AND no surprises remain. This is a strong
signal that more same-family runs are not teaching anything new.

**Watch out for:** Absolute SHAP ranks can look identical across versions
while the *deltas* tell a story — a feature that has been in the top-5
for 3 versions is not news; a feature that was rank 17 and is now rank 4
is. Single-seed SHAP is preliminary; confirm a rank shift on ≥2 seeds
before writing an implication. SHAP values are model-specific; a feature
ranked high in CatBoost may be near-zero in XGBoost on the same basis —
per-model SHAP is the only honest way to judge.

---

## PDP Shape Surprise

**Worth exploring when:** A model has produced PDPs (Iron Law #18
requirement); the DGP memo §7a contains predictions about feature shape;
any top-5 feature has a previously un-mapped PDP shape.

**What to try:** Scan PDPs on top-5 features by current importance.
Classify each as monotone, threshold, U-shaped, or non-monotone. Compare
against the DGP memo's predicted shape. Any discrepancy is a *surprise*
that either invalidates the DGP prediction or reveals a confound — both
are learnings. Record in `model-synthesis.md` §3 with the surprise flag;
surface as a §6 implication targeting §3 of the knowledge base.

**Ceiling signal:** All top-5 PDPs match prior predictions within a
domain-plausible band; no new inflection points emerge across 3 versions.

**Watch out for:** PDPs are average effects over all rows and can mask
heterogeneous subgroup behavior — a PDP that looks monotone in aggregate
may be non-monotone on one segment and inverse on another. Always check
key segments (hot/cold, firmware-version, batch-group) before treating
a PDP shape as a DGP finding. Aggregate PDPs are starting points, not
verdicts.

---

## Segment Weakness as First-Class Output

**Worth exploring when:** Every VALIDATE exit (mandatory per Iron Law
#26 §4), any time a segment appears in `knowledge-base.md` §6, or when
the overall metric improves while an obvious subgroup (cold, rare
firmware, rare batch) stays flat.

**What to try:** For each declared segment in KB §6, compute current
metric and trend over the last 3 versions. Record in
`model-synthesis.md` §4. Identify the weakest segment and answer the
question: did this version improve the weakest segment? If yes, by how
much. If no, for how many consecutive versions has the weakest segment
been flat? Flat-for-k-versions is an input to the direction-fatigue
counter (`coverage.json`).

**Ceiling signal:** All declared segments have updated trend lines; the
weakest-segment trend over 5+ versions is improving or stable at a
justified level.

**Watch out for:** This is the direct anti-laziness hook. A weakest
segment can sit flat for 6+ consecutive blends while the overall metric
moves by 0.0002 per blend — that is the exact single-metric trap Iron
Law #26 §6 exists to catch. If the weakest segment is flat for 3
versions and no candidate action is proposed, something has gone wrong
in the exploration — either the segment was misdefined, the feature
basis does not contain the right columns, or a specialist model is
needed.

---

## Model Disagreement as a Diversity Signal

**Worth exploring when:** The project produces blend OOFs (Caruana,
convex blend, stacking), or a new model family is being considered for
inclusion, or the residual correlation structure among existing members
has not been audited recently.

**What to try:** Compute residual correlation between the current
champion and each blend member. Members with residual correlation
≥ 0.95 to the champion are effectively duplicates — they cannot improve
a blend. Identify rows where two members disagree materially (prediction
delta > 0.3); group them by segment. A cluster of disagreement in one
segment is a signal that one model has found signal the other has not —
and therefore a candidate diversity axis.

**Ceiling signal:** All blend members have residual correlation < 0.95
to the champion, OR every member with correlation ≥ 0.95 has a
documented reason for inclusion (e.g. calibration variant).

**Watch out for:** Blend rejection by high residual correlation is how
"same-family sprawl" is detected mechanically. Sustained Caruana
saturation — five or more consecutive grand blends picking the same
single model from pools of 400+ candidates — is usually the 0.99-
residual-corr trap. The rCB < 0.95 rule is the escape, but the escape
usually lowers solo metric, which is the "ceiling law" in action. Do
not chase rCB < 0.95 blindly; the useful diversity zone (rCB < 0.95
AND solo ≥ 0.95 × champion) often does not exist on a saturated
feature basis. That is a pivot signal, not a debugging target.

---

## Residual Clustering Against Knowledge-Base Segments

**Worth exploring when:** A model improved the overall metric but you
cannot explain how; the weakest segment is flat and you want to know
what the model is getting wrong; you are preparing a §6 implication for
the synthesis and need concrete candidate actions.

**What to try:** Compute OOF residuals (y − ŷ) for the current champion.
Sort rows by |residual| descending; look at the top-100. Group by each
segment dimension in KB §6. Which segments are over-represented? That
is where the model is systematically wrong. Also group by KB §2
variables; any in-basis variable whose high-|residual| rows cluster at
one end of its range is a candidate for a non-linear feature or a
threshold flag.

**Ceiling signal:** The residual-error distribution is consistent with
noise (no segment over-represented by >1.5× its population share), or
every over-represented segment has a candidate-action entry in KB §6.

**Watch out for:** Residual mining is easy to overfit to — patterns in
the top-100 |residual| rows can be fold-boundary artifacts, not genuine
signal. Confirm any candidate action by running it on a hold-out split
with the same fold scheme. Also: residual clustering shines when the
model is close to saturation on a segment; it is less useful when the
model is broadly under-trained, which is a different problem.
