# Checklist: CV Scheme Decision

Decide before any feature engineering. Sign off goes into `audits/vN-cv-scheme.md`.

## Decision tree

- [ ] **Time structure present?** → `TimeSeriesSplit` (never shuffle). Train always precedes validation.
- [ ] **Grouped entities (user, patient, session, trial)?** → `GroupKFold` on the group key. Never split within a group.
- [ ] **Imbalanced target?** → `StratifiedKFold` (or `StratifiedGroupKFold` when combined with groups).
- [ ] **Small data + hyperparam selection?** → nested CV (outer for metric reporting, inner for tuning).
- [ ] **Regression with heavy-tailed target?** → consider stratified bins.

## Required fields in `audits/vN-cv-scheme.md`

- Chosen scheme + exact constructor args
- Rejected alternatives (at least 2) + why
- Group key or time column (if applicable)
- Folds, seed
- Predicted CV-holdout gap interpretation

## Persona
Validation Auditor signs. Unsigned blocks AUDIT phase entry.
