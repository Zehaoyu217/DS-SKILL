---
id: model-synthesis-v{N}
version: {N}
phase: VALIDATE
winning_run_id: <run_id>
winning_model_family: CB | LGBM | XGB | FT | Bayes | MLP | other
winning_feature_basis_id: fb-v<N>
primary_metric: <name — must match plans/v1.md pre-registration>
primary_metric_value: <float>
primary_metric_previous_best: <float>
primary_metric_delta: <signed float>
seeds_used: [<int>, <int>, <int>]
signed_by: orchestrator
skeptic_microreview: <true | false — required in competition mode when §6 updates a DGP hypothesis>
created_at: YYYY-MM-DDTHH:MM:SSZ
---

# Model synthesis — v{N}

> The mandatory distillation step. Raw diagnostics live in
> `audits/vN-model-diagnostics.md`; this file turns them into persistent
> insight that updates `knowledge-base.md`.
>
> **Gate (Iron Law #26):** competition mode blocks VALIDATE exit if this
> file is missing or fails `checklists/model-as-teacher.md`. Daily mode
> warns only.
>
> **Do not duplicate the diagnostics artifact.** This file records
> *deltas, shape-changes, and implications*, not raw tables. If you find
> yourself copying numbers from `audits/vN-model-diagnostics.md`, stop and
> re-read — you are producing the wrong artifact.

---

## 1. Metric delta table

_Required. Every segment declared in `knowledge-base.md §6` must appear._

| Metric | v{N-1} best | v{N} | Δ | σ (seed) | flagged? |
|---|---|---|---|---|---|
| primary (<name>) | <val> | <val> | <Δ> | <σ> | y/n |
| overfit_delta | <val> | <val> | <Δ> |  | y/n |
| <segment 1> | <val> | <val> | <Δ> |  | y/n |
| <segment 2> | <val> | <val> | <Δ> |  | y/n |

Flag rule: `|Δ_primary| > 2σ_seed` (primary) or `|Δ_segment| > 0.005` (segments).

**v1 note:** on the first version there is no previous best. Leave the
`v{N-1} best` column blank; the row for primary instead records the
feature-baseline value from Iron Law #19b, and the flag column records
whether the run cleared the feature baseline.

---

## 2. SHAP / importance delta

_Required if the winning model supports feature importances. If it does
not (e.g. pure Bayesian model), state so explicitly and move on._

- **Top-K changes vs v{N-1} champion** (K = 20):
  - moved up: <features that gained >5 ranks>
  - moved down: <features that lost >5 ranks>
  - new in top-K: <features>
  - dropped from top-K: <features>
- **Cross-seed importance stability:** high | medium | low
- **Any feature ranked in the top-10 whose presence surprises the domain memo (`dgp-memo.md §7a`)?** y/n, list

---

## 3. PDP observations

_Required. At minimum, PDP scan on the top-5 features by current
importance. One row per feature._

| Feature | Shape | Inflection | Surprise vs v{N-1}? | Surprise vs DGP memo? |
|---|---|---|---|---|
| <name> | monotone / threshold / U / non-monotone | <value or "none"> | y/n | y/n |

Any "surprise=y" row MUST appear in §6 implications.

---

## 4. Segment weakness scan

_Required. Every segment declared in `knowledge-base.md §6`._

For each segment:
- <segment name>: current=<val>, best_seen=<val>, trend (last 3 versions): up | flat | down
- Weakest segment this version: <name> (<value>)
- Did this version improve the weakest segment? y/n, by <Δ>
- Weakest segment trend over last 5 versions: <description>

---

## 5. Model disagreement signals

_Required if this version produced blend OOFs. Skip with explicit note
("no blend this version") otherwise._

- **Residual correlation matrix (top pairs):**
  - <model_a> × <model_b>: r = <value>
- **Cross-family disagreement hotspots:** rows where <family 1> and
  <family 2> predictions differ by >0.3 — summary by segment.
- **New diversity axis discovered this version?** y/n, description.
- **Blend weight shifts vs v{N-1}:** <which members gained / lost weight
  in Caruana or equivalent>.

---

## 6. Implications

_Required. **At least one bullet.** Empty §6 fails the gate — a run that
only moved the primary metric without any persistent learning is the
single-metric trap this law exists to prevent._

Each implication must name a concrete target in the knowledge base.

- **For KB §2 (variables):** <one line — e.g. "variable X ranked
  unexpectedly high in SHAP; mark explored=perm-importance+shap">
- **For KB §3 (hypotheses):** <one line — e.g. "DGP-04 claimed
  ambient_temp is additive; PDP shows threshold at 17.5°C → update
  DGP-04 claim to threshold-additive, set last_checked=v{N}">
- **For KB §4 (basis):** <one line — e.g. "feature Y has ~0
  perm-importance across v{N-2}, v{N-1}, v{N} → candidate for next basis
  rotation">
- **For KB §5 (insights):** <one line — e.g. "append MI-09: CB
  depth>5 regresses cold segment, confirmed on seeds 7/13/42">
- **For KB §6 (segments):** <one line — e.g. "cold segment flat for 4
  versions → surface in next Research Lead coach note">

If *no material implications* were produced this version, the orchestrator
must write a positive explanation (e.g. "we re-ran the v{N-1} champion
with 2 new seeds to confirm stability; no new structural learning expected
and none observed"). Silent emptiness is a gate failure.

---

## 7. Proposed KB patches

_Required. One line per patch. Applied by the orchestrator via
`/ds-kb apply-patches audits/vN-model-synthesis.md` after VALIDATE exit._

Format:
- §<N> <section name> — <one-line change>

Examples (generic — substitute your project's actual names):
- §2 variables — mark `<high-card-cat-column>` explored=[native-OTE, perm-importance] at v{N}
- §5 insights — append MI-0N: `<model-family>` depth>X regresses `<segment>` segment
- §6 segments — update `<segment>` trend to "flat (K consecutive versions)"

---

## Sign-off

- Orchestrator: yes
- Skeptic micro-review (competition mode, when §6 updates DGP hypotheses): <yes | n/a>
