# Knowledge Base

> The single, curated view of what we know about this dataset and this problem.
> Not a log — a living understanding. Append-only logs live in `findings/`,
> `disproven/`, `step-journal/`; this file distills those into one place a
> practitioner can read in five minutes and orient from.
>
> **Single-writer rule:** only the orchestrator writes to this file. Research
> Lead proposes patches in its coach note (`audits/vN-research-lead.md`
> §"Proposed KB updates"); the orchestrator applies them. Other personas do not
> edit this file.
>
> **Linting:** `scripts/knowledge_lint.py ds-workspace` audits this file for
> staleness, unexplored variables, unconsumed model insights, and segment
> gaps. Lint is warning-only — it does not block any phase.

---

- **Project:** <name>
- **Primary metric:** <metric — same as pre-registered in `plans/v1.md`>
- **Current version:** v<N>
- **Last full review:** v<N> (YYYY-MM-DD)
- **Lint status:** GREEN | WARN | STALE

---

## 1. Dataset profile

_Durable facts about what the data is, where it comes from, and how it was
collected. Update when the data itself changes, not when models change._

last_reviewed: v<N>

- **Source(s):** <one line each, including file paths / external joins>
- **Row count (train / internal-holdout / test):** <numbers>
- **Row grain:** <one observation represents …>
- **Time window / seasonality:** <if any>
- **Primary target:** <column, definition, label distribution, class balance>
- **Joins / merges:** <tables, keys, expected cardinality, known fan-outs>
- **Known upstream biases or collection quirks:** <text, cite sources>
- **Cross-track notes:** <if the project maintains multiple feature bases (e.g. `_a` / `_b`), name them here>

---

## 2. Variable catalog

_Every raw-input column, its current exploration state, and the open questions
against it. The Research Lead checks this first — any variable with
`explored: []` is a reason not to start another modeling run._

_Variables with `in_feature_basis: false` and no open questions may be
collapsed to a one-line summary. This is a working catalog, not a full data
dictionary._

last_reviewed: v<N>

```yaml
variables:
  - name: <col>
    type: numeric | categorical | id | datetime | sequence | text
    units: <if numeric>
    range_or_cardinality: <[min,max] or int>
    missing_rate: <float>
    in_feature_basis: true | false
    basis_role: raw | engineered_source | te_target | pruned | excluded
    explored:
      - kind: histogram | pdp | perm-importance | shap | te-stability | pairwise | segment | adversarial | residual
        vN: v<N>
        finding_ref: <finding-id | disproven-id | audit-path, optional>
        summary: <one line>
    open_questions:
      - <one-line question>
    last_reviewed: v<N>
```

---

## 3. DGP hypotheses

_What we believe generates the data, and whether each belief is alive, dead,
or pending. Cross-ref to `dgp-memo.md` for the full derivation; this is the
live scoreboard._

last_reviewed: v<N>

```yaml
hypotheses:
  - id: DGP-01
    claim: <one-line>
    status: alive | dead | pending
    evidence_for: [<finding-refs>]
    evidence_against: [<disproven-refs>]
    first_stated_vN: v<N>
    last_checked_vN: v<N>
```

---

## 4. Feature basis history

_Every time the working feature set materially changed, and why. A single
line per basis version. If the last entry is > k versions old, the Research
Lead should propose a feature-basis rotation._

last_reviewed: v<N>

| basis_id | opened_at_vN | cols_in_basis | rationale | ceiling_seen |
|---|---|---|---|---|
| fb-v1 | v1 | <N> | initial raw + minimal engineering | <metric @ vN> |
| fb-v2 | v<N> | <N> | <why> | <metric @ vN> |

---

## 5. Model-derived insights

_Distilled cross-version summary of what models have taught us. Each entry is
a persistent insight, not a per-run log (those go in `step-journal/`). An
insight is appended here only after it has held on ≥3 seeds or ≥2 model
families — single-seed, single-model observations belong in findings, not
here._

last_reviewed: v<N>

```yaml
insights:
  - id: MI-<N>
    claim: <one-line>
    source: shap | pdp | perm-importance | segment | disagreement | residual | calibration
    models_agree: [<model-ids or family names>]
    seeds_confirmed: <int>
    first_seen_vN: v<N>
    last_confirmed_vN: v<N>
    implies:
      - for: feature-engineering | data-quality | model-selection | ensemble
        suggestion: <one-line actionable>
```

---

## 6. Segment analysis

_How model performance differs across meaningful segments of the data. The
most common "lazy" failure mode is to chase overall metric while the weakest
segment stays flat — this section keeps that visible every version._

last_reviewed: v<N>

```yaml
segments:
  - name: <cold | hot | planet=X | firmware=Y | …>
    definition: <boolean expression in raw cols>
    population_share: <fraction>
    current_metric: <value @ vN>
    best_seen_metric: <value @ vN>
    trend_last_k_versions: improving | flat | regressing
    candidate_actions:
      - <one-line>
```

---

## 7. Failure mode catalog

_Patterns that broke us, or nearly broke us, so future versions recognise
them on sight. A compact summary of every `disproven-card` with non-local
generalisability, plus any external-submission mismatch, pseudo-cascade,
leakage, or gap-inflation event observed._

last_reviewed: v<N>

```yaml
failure_modes:
  - name: <short label>
    mechanism: <one paragraph>
    first_seen_vN: v<N>
    detection_signal: <what tells you this is happening now>
    mitigation: <what to do when the signal fires>
    refs: [<disproven-refs>, <lesson-refs>, <external links>]
```

---

## 8. Open questions (rolling)

_One-line items the Research Lead (or the orchestrator) has flagged but that
don't yet have owners. Oldest items at the top. Items move out of this
section when a finding, disproven-card, or audit closes them — link the
closing artifact when removing._

- [ ] Q-001 (opened v<N>): <one-line>
- [ ] Q-002 (opened v<N>): <one-line>
