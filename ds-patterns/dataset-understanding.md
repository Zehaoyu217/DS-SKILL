# Dataset Understanding Patterns

Patterns for building and maintaining a curated view of the dataset itself —
separate from modeling work. Pull this up when the baseline is lower than
the data complexity would suggest, when the orchestrator has been in
FEATURE_MODEL for many versions without revisiting the data, or when the
knowledge base shows unexplored columns.

The artifact these patterns feed is `knowledge-base.md` — the single linted
view of what is known about this dataset. `scripts/knowledge_lint.py`
surfaces gaps.

---

## Variable Catalog Discipline

**Worth exploring when:** The project is new, or the knowledge base has
variables in §2 with `explored: []`, or recent modeling runs surprise you
with unexpected SHAP rankings on rarely-examined columns.

**What to try:** Fill `knowledge-base.md` §2 (Variable catalog) with one
entry per raw column, even for columns you expect to be uninformative. For
each in-basis variable, record at least: histogram shape, missing rate,
range or cardinality, and one `explored:` entry with the kind of check
done (`histogram`, `pdp`, `perm-importance`, `shap`, `pairwise`,
`segment`, `adversarial`). Use `/ds-kb update variables` to keep the
catalog live.

**Ceiling signal:** Every in-basis variable has ≥1 `explored` entry and a
current `last_reviewed` stamp. Variables not in the basis either have an
exclusion reason (pruned / leakage-suspect) or an open question that is
being tracked.

**Watch out for:** A sparse §2 is the root of the "settle with one feature
pool" failure mode — when the orchestrator does not know what it has not
looked at, it defaults to repeating what it has looked at. The Research
Lead reads §2 first on every coach note; an empty catalog produces weak
coaching. Also: do not fill §2 with fake entries to silence the lint.
`explored: []` is a real signal; writing `explored: [histogram]` without
actually producing a histogram defeats the point.

---

## Pre-Modeling Data Profile

**Worth exploring when:** You are at FRAME or AUDIT phase and have not yet
computed basic structural facts about the dataset (row count, column types,
missing rates per column, unique counts, join cardinalities). Also when
`data-contract.md` is empty beyond the eval-harness lock.

**What to try:** Produce a structural profile from raw data before any
feature engineering: counts, dtypes, null rates, cardinalities, describe()
on numeric columns, value-count heads on categoricals, join diagnostics
for every merge in the data-prep pipeline. Write the salient facts into
`knowledge-base.md` §1 (Dataset profile) and keep `last_reviewed` stamped.

**Ceiling signal:** §1 contains row counts, target distribution, join
cardinalities, and at least one line about known upstream biases.
Adversarial AUC on raw features has been computed and logged to
`audits/vN-adversarial.md`.

**Watch out for:** A single parsing bug (unit mismatch, duplicate column
after join, silent truncation) can dominate all feature engineering
combined — one project saw +0.09 OOF from fixing a unit-mismatch bug
(milliamps vs amps in a sensor column) plus a silent duplicate-column
issue from a table join, before any feature engineering. The profile is
cheap to produce and prevents the most expensive failure mode in the
whole loop. Any time you find yourself hand-waving "the data is fine",
spend 30 minutes on this pattern.

---

## Cross-Source Sanity on Joins

**Worth exploring when:** The data pipeline joins ≥2 tables; expected row
counts do not match observed; a join introduces new columns that look
uninformative but might be fanout noise; an adversarial AUC above 0.6 was
observed after a join.

**What to try:** For every join, compute (a) input row count on both
sides, (b) output row count, (c) unique join-key counts on both sides,
(d) fanout ratio. Flag any join where output > max(left, right) — that is
fanout and will silently duplicate rows. Check that every column produced
by the join is either used downstream or explicitly pruned. Spot-check
rows where the join-key is near-unique on one side and common on the
other — those are the rows most likely to contain bad data.

**Ceiling signal:** Every join has a row-count ledger in §1 of the
knowledge base, no silent fanout remains, and every joined column either
has an `in_feature_basis` entry or a documented reason for exclusion.

**Watch out for:** Pandas silently creates `col_x` / `col_y` when a join
key collides with a data column — one project saw a +0.06 OOF gain
simply from deduplicating after a join. Joins that produce `_x` / `_y`
columns should be resolved manually; do not let them propagate into
feature engineering, and log the resolution in the knowledge base.

---

## DGP Hypotheses as a Living List

**Worth exploring when:** Entering DGP phase, or a model produces a top
feature whose mechanism you cannot explain, or PDP shape conflicts with
prior domain belief.

**What to try:** Maintain `knowledge-base.md` §3 (DGP hypotheses) with
entries in `status: alive | dead | pending`. Every hypothesis has at
least one `evidence_for:` or `evidence_against:` reference. Move a
hypothesis to `dead` only when a disproven-card explicitly refutes it.
Move to `alive` only when a finding-card is promoted to
`generalizability: promotable`. Pending hypotheses older than 3 versions
without new evidence are flagged by the linter.

**Ceiling signal:** Every top-10 feature by current SHAP has a mechanism
sentence in an `alive` hypothesis, or an `open_question` in §2 noting
that no mechanism is yet known.

**Watch out for:** Hypotheses are the bridge between the Domain Expert
persona and the modeling work. A hypothesis with `status: pending` that
nobody is tracking will drift with the project; either upgrade, kill, or
remove. The Research Lead coach note uses §3 as a direction source —
empty §3 produces vague coaching.

---

## Scheduled Knowledge-Base Rotation

**Worth exploring when:** The `last_reviewed` stamp on any KB section is
older than `state.current_version - 5`, or `knowledge_lint.py` surfaces
`kb.section-stale` warnings, or `/ds-kb` shows more than a handful of
open gaps.

**What to try:** Once every 5 versions (or sooner if the linter fires),
walk each section of `knowledge-base.md` and update it against the latest
findings, disproven-cards, and model-synthesis audits. Apply any pending
`/ds-kb apply-patches` from Research Lead or model-synthesis files. Bump
`last_reviewed` on every section you actually review — do not bump a
stamp you did not touch.

**Ceiling signal:** All section stamps are within the last 5 versions;
`knowledge_lint.py` emits no `kb.section-stale` warnings; no audit has
unapplied `## Proposed KB patches` older than 2 versions.

**Watch out for:** Bumping `last_reviewed` without actually reviewing the
section is knowledge-base rot. The stamp is a load-bearing signal for
the linter and the Research Lead; treating it as ceremony defeats the
entire mechanism. If you do not have time to review a section, leave the
stamp alone — a stale stamp is a signal, not a failure.
