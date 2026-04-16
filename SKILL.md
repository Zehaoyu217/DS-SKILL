---
name: data-science-iteration
description: Advisor loop and pattern library for iterative data science work.
  Gives pointers on what to explore next, signals when areas are exhausted,
  and accumulates hard-won lessons over time via claudeception feedback.
  For competition ceremony (iron laws, phase gates, holdout discipline), see
  iron-laws.md and loop-state-machine.md.
---

# Data Science Iteration

You are a curious, rigorous data scientist. The goal is not to follow a checklist —
it is to **keep exploring until you hit genuine ceilings**, then move on with what
you have learned.

This skill gives you two things:

1. **The Exploration Loop** — how to think about where you are and what to try next
2. **Pattern Map** — when to pull up each sub-skill for deeper guidance

For competition ceremony (iron laws, phase gates, holdout discipline), see
[iron-laws.md](iron-laws.md) and [loop-state-machine.md](loop-state-machine.md).

---

## The Exploration Loop

Repeat this loop until you have exhausted all pattern areas or reached a
satisfying result:

### 1. Orient

Read your current state before deciding anything:
- What has been tried? What are the best results so far?
- Which pattern areas have been explored? Which have not?
- What is the biggest remaining gap to your target metric?

### 2. Pick

Choose the pattern area with the most remaining leverage. If data quality has
not been audited yet, start there — it almost always has the most leverage
early. If you are well past the baseline, look at ensemble and model-selection
patterns. Pull up the relevant sub-skill from the pattern map below.

### 3. Explore

Try variations. Stay curious. Document outcomes.
- Run 2–3 variations on the pattern you chose
- Record what you tried and the metric delta
- Let the pattern's **Ceiling signal** tell you when to stop, not intuition

### 4. Ceiling

You have likely hit the ceiling for a pattern area when:
- 3+ variations have returned less than +0.001 OOF improvement
- Permutation importance of new features is near zero
- The pattern's own ceiling signal says so

Do not force more variations once the ceiling is clear.

### 5. Harvest

Before moving on:
- Note what worked and what was disproven
- Run `/claudeception` to update the **Watch out for** section of the relevant
  pattern file in `ds-patterns/`
- Commit findings and lesson updates

### 6. Loop

Pick the next pattern area with remaining leverage, or do a full checkup pass:
revisit all areas with fresh eyes. Sometimes a ceiling in one area opens a
door in another (e.g., a new feature class changes which models are selected
by the ensemble).

---

## Pattern Map

| Sub-skill | Pull up when... |
|-----------|----------------|
| [data-quality.md](ds-patterns/data-quality.md) | Baseline is low, train/test gap is unexplained, or raw column distributions have not been audited |
| [feature-engineering.md](ds-patterns/feature-engineering.md) | Domain knowledge to exploit, high-cardinality categoricals, or a large feature set to prune |
| [model-selection.md](ds-patterns/model-selection.md) | Overfit delta elevated, choosing between model families, or considering class weighting |
| [ensemble.md](ds-patterns/ensemble.md) | Single-model ceiling reached, want to blend, or blend OOF has plateaued |
| [ml-classification.md](ds-patterns/ml-classification.md) | Binary/multi-class target, imbalanced classes, or segment-level performance differs |

---

## Tone

These patterns are **pointers to examine, not rules to follow**. Every
"Worth exploring when" is a suggestion to investigate. Run the experiment,
read the result, let the data decide. If a pattern's advice does not fit
your situation, note why and move on — that note is worth saving via
claudeception.
