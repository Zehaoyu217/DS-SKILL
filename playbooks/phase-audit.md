# Phase: AUDIT

## Entry gate
DGP exited (`dgp-memo.md` signed by Skeptic + Validation Auditor + Domain Expert (or recorded waiver) AND `audits/vN-debate-dgp.md` has `verdict: consensus-pass` AND zero open CRITICAL findings across the three DGP audits).

## Purpose
Deep data quality audit and leakage sweep before any modeling work. Establish baseline data integrity, confirm no information leakage is present in existing code, measure train-vs-test distribution shift, and lock the eval harness so any future modification is detectable. Record data hash for reproducibility tracking.

## Steps (in order)
1. Run data QA report: check missingness, data types, units, duplicate keys, time gaps. Write findings to a new section in `audits/vN-data-qa.md`.
2. Validation Auditor runs [checklists/leakage-audit.md](../checklists/leakage-audit.md) grep on any existing `src/` code; document patterns found in `audits/vN-leakage.md`.
3. Compute sha256 hash of the full dataset and record in `runs/vN/data.sha256` for reproducibility gates.
4. **Adversarial validation (Iron Law #13).** Run [checklists/adversarial-validation.md](../checklists/adversarial-validation.md): train a classifier to distinguish train vs. test rows, report AUC and duplicate ratio. Write results to `audits/vN-adversarial.md`. If AUC > 0.60, fire the `covariate-shift` event — CV scheme may need revision before DATA_PREP proceeds. See [event-covariate-shift.md](event-covariate-shift.md) and [scripts/adversarial_validation.py](../scripts/adversarial_validation.py).
5. **Lock eval harness (Iron Law #20).** Write the eval harness hash into `data-contract.md`:
   ```
   python $SKILL/scripts/hash_eval_harness.py <ds-workspace>
   ```
   This records `src/evaluation/` sha256. Future phases run `--check` at entry; any mismatch fires `eval-harness-tampered`. Exit 2 means `src/evaluation/` doesn't exist yet — create your primary metric function in `src/evaluation/` before running this step.
6. If any data quality or leakage issue is found, file a new hypothesis or event into the appropriate playbook (open v(N+1) if blocking).

## Persona invocations
- **Validation Auditor** (primary): Run leakage audit, data QA, and adversarial validation. Output: `audits/vN-leakage.md` with Verdict [PASS | BLOCK] and `audits/vN-adversarial.md` with AUC + duplicate ratio.
- **Skeptic** (optional, if called on surprising data patterns): Review data structure and hypothesis of surprises.

## Exit gate
`audits/vN-leakage.md` Verdict=PASS AND data quality issues resolved or documented AND `audits/vN-adversarial.md` present (AUC and duplicate ratio recorded) AND eval harness hash written to `data-contract.md` (`scripts/hash_eval_harness.py` write mode exits 0).

## Events that can abort this phase
- `leakage-found` (audit hits a leak pattern; mark affected runs and open v(N+1))
- `assumption-disproven` (data contradicts framing; update data-contract and open v(N+1))
