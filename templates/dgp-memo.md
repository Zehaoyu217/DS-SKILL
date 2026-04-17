# DGP Memo v{N}  (parent: v{N-1} | root)

> "What is the true data-generating process here?"
> A signed artifact that names the mechanism behind each field, the selection filter that produced the training sample, and the axes along which train and test will differ. Leakage found by grep is code leakage; leakage found here is structural leakage.

## 1. Target definition
- Exact definition, units, time-of-measurement relative to features.
- Who/what records this label? Manual, automated, delayed, self-reported?
- Known ambiguity or definition drift across time/region/cohort.

## 2. Feature provenance table
| Field | Source system | Captured when (relative to label event) | Generator | Can it leak? |
|---|---|---|---|---|
| ... | ... | <pre-label / at-label / post-label> | <human / sensor / derived> | <yes/no + why> |

Any field with "Captured when = at-label or post-label" is suspect. Justify retention explicitly or drop.

## 3. Selection mechanism
- Who ends up in the training sample? What filter was applied upstream?
- Survivorship bias, response bias, sampling windows, platform effects.
- If the organizer's test set is drawn differently from train, list the delta.

## 4. Confounds and upstream/downstream graph
Sketch (or DAG) of target ← causes ← upstream; target → downstream → features that look predictive but are post-hoc.
List the three most dangerous backdoor paths.

## 5. Expected distribution shift axes (train → hidden test)
- Time shift: <yes/no + which columns>
- Population shift: <yes/no + which segments>
- Measurement shift: <yes/no + which instruments>
- Label-prevalence shift: <yes/no + expected magnitude>
Each axis names a concrete check (e.g., adversarial-validation AUC on suspected drift columns).

## 6. Priors from literature / domain

**Primary empirical input:** `runs/v{N-1}/learnings.md` "Summary at close" block (for v2+). Read this first — it contains belief updates from the previous version's actual data, which carry more weight than prior literature for established problem classes.

Then cite at least 3 sources (Kaggle writeup, paper, prior-version learnings entry, or domain-expert claim). What effect sizes are plausible? What have others tried that failed?

For each source, note: source type (literature | prior-version-learning | domain-expert), what prior it updates, and in which direction.

## 7. Predictions the model should make (story check)
If the model is good, which features should dominate in which direction? Name 3–5 expected SHAP/coefficient signs. A later **Narrative Audit** compares actual importances to these predictions.

### 7a. Structured predictions (machine-readable)

Each prediction gets an id `P-NNN`. Findings and disproven-cards reference these ids via `dgp_refs[].prediction_id` so `scripts/consistency_lint.py` can detect contradictions.

```yaml
predictions:
  - id: P-001
    subject: <feature or feature-group name>
    direction: positive | negative | non-monotonic | interaction
    magnitude: small | medium | large | unknown
    rationale: <one line — why we expect this from DGP / literature>
    priority: top | secondary
      # top predictions are checked at narrative audit; secondary are informational
  - id: P-002
    subject: ...
    direction: ...
    magnitude: ...
    rationale: ...
    priority: ...
```

## 8. Kill-switches
If any of the following turns out false, the DGP memo is wrong and a v(N+1) must reopen framing:
- [ ] ...
- [ ] ...

## Sign-offs
- Skeptic: [pending|signed]
- Validation Auditor: [pending|signed]
- Domain Expert: [pending|signed|waived-with-rationale]
- Literature Scout (Lite memo cross-referenced): [pending|signed]
