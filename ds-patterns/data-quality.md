# Data Quality Patterns

Patterns for assessing and fixing data before feature engineering.
Pull this up when your baseline is lower than expected, train/test
performance gaps are puzzling, or you haven't yet audited your raw columns.

---

## Data Cleaning Before Feature Engineering

**Worth exploring when:** Your baseline metric is lower than the data complexity
would suggest, or there is an unexplained gap between CV and leaderboard/holdout
performance.

**What to try:** Before engineering new features, it is worth running a quick
sanity check on each raw column: check numeric ranges for implausible values,
spot-check train vs test distributions, and verify any columns that are parsed
from strings (suffixes, decimal precision, comma-separated values). Consider
whether any joins (external tables, time-series merges) could be inflating row
counts or introducing duplicates.

**Ceiling signal:** All numeric columns have plausible unimodal distributions
within expected domain ranges; train/test adversarial AUC ≤ 0.55 on raw
features; no join inflation detected; null rates match between train and test.

**Watch out for:** A single parsing bug can dwarf all feature engineering
combined — a unit mismatch in one sensor column (milliamps vs amps) added
+0.089 OOF when fixed, larger than any subsequent feature engineering step.
Prioritise data quality audits before building features, especially when the
baseline feels lower than it should be.

---

## Train/Test Distribution Drift

**Worth exploring when:** Model performs well in CV but poorly on holdout or
leaderboard; adversarial validation AUC > 0.6; certain features have different
ranges or cardinalities in train vs test.

**What to try:** Train a binary classifier (any fast tree model) to separate
train from test samples using raw features. The top features by importance in
that classifier are your drift suspects. For each suspect: compare histograms,
check decimal precision differences, look for format noise (e.g., one set has
trailing decimals, the other does not). Consider harmonising to the coarser of
train/test precision.

**Ceiling signal:** Adversarial AUC drops to ≤ 0.55 after harmonisation;
no remaining features show materially different distributions between train
and test.

**Watch out for:** Even cosmetic format differences (e.g., one dataset rounds
voltage to integers, the other keeps two decimal places) can produce adversarial
AUC of 0.99+, effectively making the model treat those columns as ID features.
Harmonise format noise early — it is easy to miss because the column passes all
type checks and looks numeric.

---

## Parsing and Unit Bugs

**Worth exploring when:** A numeric column has an implausibly wide range
(max/min ratio > 1000), a bimodal distribution with no domain explanation,
or unusually high correlation with the target that domain knowledge cannot
explain.

**What to try:** Plot histograms for all numeric columns and flag any where
the distribution looks bimodal or has extreme outliers. For string-formatted
numeric columns, check for mixed unit suffixes (e.g., "100mA" vs "0.1A").
For any column suspected of unit mixing, apply a threshold rule (e.g., values
above N are in unit X, values below are in unit Y) and verify the corrected
distribution is unimodal.

**Ceiling signal:** All numeric columns have unimodal, domain-plausible
distributions; no suffix patterns found; no max/min outlier flags remain.

**Watch out for:** Mixed-unit columns silently corrupt every derived feature
that uses them (e.g., I²R power calculated with milliamps instead of amps
is wrong by a factor of 10⁶). The column looks numeric and passes type checks —
only the distribution shape or domain knowledge reveals the bug. Fix parsing
at the earliest stage of the pipeline before any feature derivation.

---

## Anomaly Flag Prevalence Threshold

**Worth exploring when:** You are considering adding null/outlier/anomaly
indicator flags (e.g., `is_voltage_null`, `is_current_anomalous`) as features
to the model.

**What to try:** Before adding any flag feature, compute its prevalence (% of
rows where the flag is 1). Only add flags with prevalence above ~5%. For flags
below that threshold, check whether the signal they capture is already encoded
in the raw column's distribution.

**Ceiling signal:** All remaining candidate flags are below 5% prevalence;
permutation importance of existing flag features is consistently near zero.

**Watch out for:** Flags with <2% prevalence show zero importance across all
tree model families — they add no signal and occupy feature space. The 5%
threshold is a rough lower bound, not a guarantee of signal. Always validate
new flags with permutation importance after adding them; prune any with
negative importance immediately.
