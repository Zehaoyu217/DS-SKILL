# Idea Research Patterns

Patterns for finding new ideas, hypotheses, and approaches when you are
stuck or want to explore beyond what you already know.
Pull this up when you have hit ceilings across multiple pattern areas,
when a problem type is unfamiliar, or when you want to pressure-test your
current approach against what others have done.

---

## Prior Work Search

**Worth exploring when:** You are about to engineer features or try a model
architecture for a domain you haven't worked in before; or you have hit a
ceiling and want to know if anyone has published a solution to a similar
problem.

**What to try:** Search in this order — (1) **Kaggle** for notebooks and
discussion threads on the same domain or target variable type (search by
dataset tags, column names, or problem description); (2) **GitHub** using
`gh search repos` and `gh search code` for implementations of the specific
technique or domain (e.g., "predictive maintenance XGBoost", "tabular
classification sensor data"); (3) **arXiv** for recent papers on the specific
domain or feature engineering technique (use abstract search with domain
keywords + "tabular" or "classification"). For each source found, identify
the core idea — not the full implementation — and form a testable hypothesis
before building anything.

**Ceiling signal:** 3+ sources searched, no materially new technique found
that isn't already in the current feature or model pipeline; all promising
ideas from prior work have been tried or explicitly ruled out.

**Watch out for:** Don't copy approaches blindly — understand *why* a technique
worked in the source context before applying it. Many Kaggle solutions are
dataset-specific tricks that don't generalise. Focus on the underlying
mechanism (e.g., "they used target encoding for high-cardinality categoricals
because the category-level failure rate varied 5x") rather than the
implementation detail. Also: the fact that a technique is popular in prior
work does not mean it will work here — treat it as a hypothesis to test,
not a confirmed improvement.

---

## Hypothesis Generation from First Principles

**Worth exploring when:** You are stuck and don't know what to try next;
your pattern areas feel exhausted; or you want to systematically generate
new feature ideas beyond what you've already derived.

**What to try:** Structured brainstorm from the data-generating process:
(1) **Write down what physically/logically causes the target** — what
mechanisms produce a failure, an outcome, or a label change? Each mechanism
is a candidate feature or interaction. (2) **List what you are NOT measuring**
that might correlate with the target — missing sensors, latent variables,
proxy signals. Are any of them recoverable from existing columns? (3) **Ask
what changes over time or across groups** in the data — regime changes,
cohort effects, seasonal patterns. Can you encode those as features? (4) For
each hypothesis, write it as a testable claim: "If [mechanism], then
[feature X] should correlate with target, especially in [subgroup Y]."

**Ceiling signal:** Brainstorm list is exhausted; all testable hypotheses
have been tried or have permutation importance near zero; domain expert review
confirms no obvious mechanisms are unencoded.

**Watch out for:** Hypothesis generation without grounding in the DGP quickly
drifts into combinatorial explosion — trying every pairwise interaction, every
ratio, every polynomial. This wastes time and adds noise. Ground every
hypothesis in a mechanism: "I believe X causes Y because Z." If you cannot
state the mechanism, the hypothesis is not worth testing. Also: hypotheses
that survive the DGP check but fail in the data are still valuable — document
them as disproven with the observed OOF delta.

---

## Competition Solution Mining

**Worth exploring when:** You are working on a tabular ML problem and have
hit ceilings on standard patterns; the problem type (imbalanced classification,
time-series, sensor data, etc.) has a Kaggle competition history; you want
to see what gold-medal solutions used that is not in standard literature.

**What to try:** Search for the top 3–5 writeups from competitions with the
most similar problem structure (same domain, similar features, similar target).
Focus on: (a) what feature engineering choices were novel or counter-intuitive;
(b) what model families dominated (and which were surprisingly absent);
(c) what ensemble or stacking architectures worked; (d) what the gold-medal
solutions explicitly say *did not* work. Extract the key ideas as hypotheses
and rank them by how well they match your DGP before trying any.

**Ceiling signal:** Top 5 relevant competition writeups read; key ideas
extracted and either tried or explicitly ruled out based on DGP mismatch;
no remaining untested ideas that match your problem structure.

**Watch out for:** Competition solutions are optimised for the leaderboard
metric on a specific dataset — they often include aggressive leakage of
public leaderboard information, ensemble complexity that would never generalise,
and dataset-specific tricks. Extract the *principle* (e.g., "pseudo-labelling
helped when the test set had a different distribution") not the implementation.
Also note what the writeup says didn't work — that negative knowledge is
often more transferable than the winning tricks.

---

## Systematic Feature Idea Backlog

**Worth exploring when:** You want a living list of untested feature ideas
rather than ad-hoc brainstorming; you are starting a new version and want
to prioritise what to try.

**What to try:** Maintain a short backlog of feature hypotheses, each with:
(1) the mechanism (why it might help), (2) the implementation sketch (what
column or transform), and (3) a priority score (estimated lift × ease of
implementation). Before each new version, pick the top-priority untested
hypothesis. After each version, update the backlog — mark hypotheses as
confirmed, disproven, or deferred, and add any new ideas generated during
that version's exploration.

**Ceiling signal:** Backlog is empty or all remaining hypotheses have
estimated lift below +0.001; all high-priority hypotheses tried; no new
mechanisms identified from DGP review or prior work search.

**Watch out for:** Backlogs become stale if not maintained after each version.
A hypothesis that made sense at version 10 may be irrelevant at version 50
once the feature space has changed. Periodically prune hypotheses that are
no longer plausible given what has been learned. The backlog is a prioritised
queue, not a dumping ground — keep it short enough to be actionable (≤10
items at any time).
