# Phase: DATA_PREP

## Entry gate
AUDIT exited (`audits/vN-leakage.md` Verdict=PASS AND `audits/vN-adversarial.md` present).

## Purpose
Systematic data cleaning, preprocessing, and transformation before EDA or modeling. Most data science failures trace back to silent data quality issues — mixed types, inconsistent encodings, join fanouts, outliers that dominate a model, or missing values handled in ways that leak information. This phase makes every cleaning decision explicit, auditable, and reproducible.

This phase does NOT decide features or fit models. It produces clean, well-typed, documented data assets that the EDA and FEATURE_MODEL phases consume.

## Brainstorm precedence (Iron Law #25 over #19a)

At **v=1**, Iron Law #19a applies unconditionally: brainstorm ≥3 alternatives per
>5%-missing column and per every other brainstorm-required step in this playbook.

At **v≥2**, read `coverage.json` first (Iron Law #25). For each brainstorm step below:
- If the relevant pattern area (`data-quality` for missing/outlier/duplicate decisions)
  is marked `exhausted: true` with a documented `ceiling_reason` AND no new column has
  crossed the >5%-missing threshold since last version, the per-column brainstorm is
  optional — reference the prior version's brainstorm file and note "coverage-exhausted;
  no new alternatives required" in the rationale cell.
- If the pattern area is not exhausted OR a new column now exceeds the threshold,
  treat it as v=1 and run the full ≥3 brainstorm.
- If ALL pattern areas are exhausted, the orchestrator fires `auto-defeat` (Iron Law #22)
  rather than permit empty brainstorm entries.

The consistency linter reads `coverage.json` and refuses to accept a blank brainstorm
without either (a) the exhaustion citation or (b) the new-column trigger.

## Steps (in order)

0. **Raw-data baseline snapshot.** Load raw data. Record row count, column count, per-column dtype, per-column null rate, basic summary stats, and raw-data hash (`data.sha256.raw`) into `runs/v{N}/data_baseline.txt`. This is the pre-prep reference state; all prep decisions will be diffed against it at step 7.

0.5. **Explorer dispatch (advisory, non-blocking).** Launch Explorer as an independent subagent to brainstorm domain-specific data-quality concerns and unusual cleaning strategies for this problem class. Explorer output → `audits/v{N}-explorer-data-prep.md` with ≥3 candidate ideas (e.g., "if this is medical data, missingness may be MNAR by severity", "for this retail domain, outliers at price=0 may be promotional free-SKUs and should be flagged not dropped"). Orchestrator reads this *before* step 2 brainstorm.

1. **Schema audit.** For every column: verify dtype matches the data contract (`data-contract.md`). Flag mixed-type columns (e.g., numeric column with string sentinels like "N/A", "missing", "-"). Log findings to `audits/vN-data-prep.md` §1.

2. **Missing value census + brainstorm.** For every column with missing data, compute missing rate and determine missingness mechanism (MCAR / MAR / MNAR) where possible. **For every column with >5% missing, write a `runs/v{N}/brainstorm-v{N}-DATA_PREP.md` entry with ≥3 handling strategies considered**, using the [brainstorm template](../templates/brainstorm-vN.md). Candidate strategies to consider (not all apply to every column):
   - Drop column (if missing rate > threshold, default 80%, adjustable in plan)
   - Drop rows (if missing rate < 1% and rows are not systematically different)
   - Impute with median/mode (simple, low-risk default)
   - Impute with model-based method (flag: must respect CV folds — no fit on full data, Iron Law #3)
   - Leave as-is for tree-based models (document why)
   - Create missingness indicator feature (document hypothesis for why missingness is informative)
   - Domain-specific strategy proposed by Explorer in step 0.5

   The chosen strategy and rationale (including rejected alternatives) go into `audits/vN-data-prep.md` §2 with a pointer to the brainstorm entry. §2 MUST use the **signed-rationale table format** below — one row per column with >5% missing, with every field filled (no blanks, no "TBD"):

   ```markdown
   ## §2 Missing-value handling (signed rationale)

   | Column | Missing rate | Mechanism (MCAR/MAR/MNAR + evidence) | Strategy chosen | Strategies rejected (+ brainstorm ref) | Leakage risk assessed | Signed-by (Engineer) |
   |---|---|---|---|---|---|---|
   | age | 12.3% | MAR; older rows missing with date | Median impute within fold | A2 model-based (cost), A3 drop-rows (loses 12% of data) — see brainstorm-v{N}-DATA_PREP.md §age | Fold-respecting; no target leakage | <name / agent-id + date> |
   | ... | ... | ... | ... | ... | ... | ... |

   Validation Auditor counter-sign: <name / agent-id + date> — "no leakage patterns introduced by §2 decisions"
   ```

   Every brainstorm alternative must be addressable — the "Strategies rejected" cell either names the rejected alternative IDs from the brainstorm file, or writes "none — deterministic case, no brainstorm required" with a one-line justification. A blank cell fails the exit gate.

3. **Duplicate detection and handling.** Exact duplicates (all columns identical): count and decide keep-first / drop-all / flag-for-review. Near-duplicates (same key columns, different values): investigate which is canonical. For multi-table joins: check for fanout (1:N producing duplicated rows) and document grain after join. Log to §3.

4. **Outlier assessment.** For numeric columns: compute IQR-based and z-score-based outlier counts. Do NOT automatically remove outliers — document each outlier population and decide:
   - Keep (real data, model should learn from it)
   - Cap/winsorize (extreme values disproportionately influence linear models; document threshold)
   - Investigate (may indicate data quality issue upstream)
   - Segment (outlier population may need separate treatment)
   Record decisions in §4.

5. **Type coercion and normalization.** Parse dates to datetime; standardize categorical string values (trim, lowercase, map synonyms); convert numeric strings to numbers; handle currency/unit inconsistencies. All transformations recorded in `src/data/prep.py` (or equivalent) — NOT done ad-hoc in notebooks.

6. **Multi-table join strategy** (if applicable). Document join keys, join type (left/inner/cross), expected grain after join, and validate row count pre/post join. Flag any unexpected row count changes (fanout or drop). Record in §5.

7. **Data prep audit sign-off.** Engineer reviews `src/data/prep.py` for reproducibility (no hardcoded paths, respects seed, idempotent). Validation Auditor confirms no information leakage in prep steps (e.g., imputation fit on full data including holdout, target-aware transformations before split). Write `audits/vN-data-prep.md` with Verdict.

## Persona invocations
- **Explorer** (entry, advisory): Brainstorm unusual / domain-specific cleaning strategies before procedural steps begin. Output: `audits/v{N}-explorer-data-prep.md`. Non-blocking.
- **Engineer** (primary): Implement all cleaning and transformation logic in `src/data/prep.py`. Ensure reproducibility (deterministic, seed-aware, idempotent). Maintain the brainstorm entries for columns with >5% missing. Output: `src/data/prep.py` + `audits/vN-data-prep.md` + `runs/v{N}/brainstorm-v{N}-DATA_PREP.md`.
- **Validation Auditor** (parallel): Verify no leakage in prep steps. In particular: imputation must not fit on holdout rows; scaling must not fit on full data; categorical mappings must not use target statistics. Output: updated `audits/vN-leakage.md` if new patterns found.

## Output artifacts
- `runs/v{N}/data_baseline.txt` — raw-data snapshot from step 0 (row/col counts, dtypes, nulls, summary stats, raw hash)
- `audits/v{N}-explorer-data-prep.md` — Explorer's domain-specific brainstorm (advisory)
- `runs/v{N}/brainstorm-v{N}-DATA_PREP.md` — per-column handling-strategy brainstorm entries (≥3 alternatives each for cols with >5% missing)
- `src/data/prep.py` — all cleaning and transformation logic, callable from any downstream phase
- `audits/vN-data-prep.md` — sections §1–§5 documenting every decision with rationale. §2 (missing-value handling) MUST use the signed-rationale table format defined in step 2, with every column filled and counter-signed by Validation Auditor for leakage. Rejected alternatives point back into the brainstorm file.
- Updated `data-contract.md` — amended with post-prep schema, row counts, and any columns dropped
- **Appended to `plans/v{N}-updates.md`** — one revision block at DATA_PREP exit summarizing any plan changes triggered by prep surprises (e.g., a column we expected to use was 95% missing → hypothesis revision)

## Exit gate
All of the following must hold (ALL AND):
- `audits/vN-data-prep.md` signed by Engineer, Verdict=PASS
- §2 (missing-value handling) present in signed-rationale table format, one row per >5%-missing column, Validation Auditor counter-signed
- Validation Auditor confirms no new leakage patterns
- `src/data/prep.py` exists and is callable from downstream phases
- `data-contract.md` updated with post-prep row count and column list
- `runs/v{N}/data_baseline.txt` present (raw snapshot from step 0)
- `runs/v{N}/brainstorm-v{N}-DATA_PREP.md` present with ≥3 alternatives per >5%-missing column (or explicit "no-brainstorm-needed" note with rationale for deterministic cases)
- `plans/v{N}-updates.md` has a revision block appended at this milestone (may be "no changes triggered" if prep produced no surprises)
- `runs/v{N}/learnings.md` has a DATA_PREP exit entry appended
- If `audits/v{N}-explorer-data-prep.md` present, its frontmatter `candidate_count >= 3` (linter warns `lint.explorer-count-low` otherwise)

## Events that can abort this phase
- `leakage-found` (prep step leaks target or holdout information; remediate and re-audit)
- `assumption-disproven` (data quality issue invalidates a framing assumption; update data-contract and open v(N+1))

## Mode differences
Identical in competition and daily modes. Data prep discipline is never optional — it is the foundation everything else builds on.
