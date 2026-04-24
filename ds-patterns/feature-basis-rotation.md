# Feature Basis Rotation Patterns

Patterns for deliberately periodically re-selecting the working feature
set instead of iterating on models against a frozen basis. Pull this up
when the feature basis has not changed in ≥5 versions, when `/ds-kb`
shows §4 (Feature basis history) without a recent entry, when
`coverage.json` shows the `feature-basis-rotation` pattern area is
unexplored, or when `ds-stale-basis-check.sh` has been firing.

The direct failure mode these patterns address is the frozen-basis trap:
the orchestrator converges to one basis early and then optimizes models
against it indefinitely. Projects have been seen running 100+ versions
on a basis that was never revisited once it was committed.

---

## Scheduled Basis Re-Selection

**Worth exploring when:** `knowledge-base.md` §4 (Feature basis history)
has no entry in the last 5 versions, OR the current basis is older than
5 versions and the last 3 champions share the same SHAP top-10, OR
`direction_fatigue_counter` for the `feature-engineering` pattern area
has crossed its threshold without a basis change.

**What to try:** Fork the current version as `vN.a` (existing basis)
and `vN.b` (rotated basis). For the rotated basis, redo permutation
importance on the current champion on the full engineered column set
(before the last prune), then re-select the top-K with fresh eyes.
Train the same model family on both bases with the same seeds. If the
rotated basis reaches within 2σ of the existing basis, promote it and
write a §4 entry. If not, write a disproven-card for the rotation and
reset the fatigue counter.

**Ceiling signal:** 2+ rotation attempts in a row return basis within
2σ of existing with no material SHAP shift — signal that the basis has
converged.

**Watch out for:** SHAP-pruning too aggressively on one rotation can
remove weak-but-real features that were compensating for each other. A
common failure: cut top-50 → solo metric improves +0.002 → cut top-25 →
solo metric collapses −0.005 because three features at ranks 26-35 were
jointly carrying a segment-level signal. Rotate with ≥2 cut depths
(top-100, top-150) and compare before committing.

---

## Per-Model SHAP, Not Shared

**Worth exploring when:** A rotated basis is being built from SHAP
pruning, OR the project currently uses one SHAP list across multiple
model families (CB, LGBM, XGB sharing one top-K), OR LGBM/XGB perform
markedly below CB in the current ensemble.

**What to try:** For each model family in the current blend, compute
SHAP on its own trained champion, and prune to per-family top-K. Train
each family on its own basis. Compare the per-family-basis blend to the
shared-basis blend on OOF. If per-family-basis wins, promote it as the
new standard.

**Ceiling signal:** Per-family-basis blend OOF is within 2σ of shared
basis AND the shared-basis OOFs have confirmed residual diversity.

**Watch out for:** Using one model family's SHAP list to prune features
for a different family can cost +0.002–0.003 per family versus
per-family SHAP — one project sustained exactly that gap for 24
versions before it was caught. Shared SHAP feels efficient but is a
silent under-performance. Per-family SHAP is cheap to compute and
usually worth the upfront cost, especially when the families are
architecturally different (shallow GBDT vs attention-based neural nets
typically need different feature preparations).

---

## Branch Testing via vN.a / vN.b

**Worth exploring when:** A basis rotation is being considered but you
do not want to abandon the incumbent basis yet, OR the loop-state machine
permits parallel branches (Iron Law #15) and you want to exploit it.

**What to try:** Open `plans/vN.a.md` and `plans/vN.b.md` with the same
model family and seeds, different bases. Run both to VALIDATE. In the
MERGE phase, pick the winner by CV with uncertainty (not by eyeballing
a single mean); emit a disproven-card for the loser. Log the outcome in
KB §4. The entire sequence takes one version's budget, not two.

**Ceiling signal:** Three consecutive basis-rotation branch tests return
loser with CV mean ≥2σ below winner — the basis has converged and
rotation is no longer the bottleneck.

**Watch out for:** Branch testing requires the Engineer to structure
`runs/vN.a/` and `runs/vN.b/` cleanly — if both branches share code that
depends on the basis (feature-building scripts), a change during one
branch can silently affect the other. Keep the branches fully isolated:
separate build_features() call, separate SHAP list, separate metrics.json.
Iron Law #15 MERGE emits disproven-cards for dropped ideas; honor it.

---

## Prune-and-Add Cadence

**Worth exploring when:** A rotated basis has been committed; model-
synthesis §2 from recent versions surfaced new candidate features from
residual clustering or segment analysis; the current basis is >150
features and overfit delta is elevated.

**What to try:** Treat basis rotation as two moves in sequence: first
*prune* (remove features with confirmed negative or zero permutation
importance across 2 seeds), then *add* (introduce ≤5 new features
generated from the last 2 synthesis §6 implications). Run the champion
on the pruned-only basis first to separate the prune lift from the add
lift. If prune improves OOF by >+0.001, commit prune, then evaluate add.
If prune is neutral, still commit it (it reduces overfit delta and
improves training speed) and evaluate add separately.

**Ceiling signal:** 2 consecutive prune-and-add rounds return
prune=neutral AND add=neutral — signal that the feature space has
saturated.

**Watch out for:** Adding features without pruning is how a project
grows to a 300+-column basis with dozens of correlated near-zero-
importance columns; pruning without adding is how you end up pruning
away weak features that were carrying residual segment signal. The two
must be balanced. A prune-and-add round is cheaper than a full basis
rotation and should be the default cadence; full rotation is reserved
for when prune-and-add has saturated.

---

## Detecting Basis Rot

**Worth exploring when:** Reviewing `knowledge-base.md` §4 at a
scheduled KB rotation, OR `ds-stale-basis-check.sh` hook has fired at
least once, OR the last 3 model-synthesis §2 blocks all say "top-20
SHAP stable".

**What to try:** Three rot signals, any one of which should trigger a
rotation proposal: (1) SHAP top-20 has been identical across 3 champions;
(2) permutation importance of the bottom quartile of the basis has
been ≤0.0001 for 3 versions (dead weight); (3) adversarial AUC on the
current basis has drifted above 0.6 on the test slice (basis is
tracking a leak or a shift axis). Record the detected signal in KB §4
with the version of detection.

**Ceiling signal:** All three signals quiet for 3 consecutive
versions — basis is stable and productive.

**Watch out for:** The hook is defensive — it will go silent if
`leaderboard.json` does not tag runs with `feature_basis_id` and
`model_family`. Make sure the tracker_log writes those fields; otherwise
the hook cannot judge and the failure mode hides. See
`leaderboard.schema.json` v2.
