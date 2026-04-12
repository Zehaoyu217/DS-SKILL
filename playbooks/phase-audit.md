# Phase: AUDIT

## Entry gate
FRAME exited (both `audits/v1-skeptic.md` PASS and `audits/v1-cv-scheme.md` signed).

## Purpose
Deep data quality audit and leakage sweep before any modeling work. Establish baseline data integrity and confirm no information leakage is present in existing code. Record data hash for reproducibility tracking.

## Steps (in order)
1. Run data QA report: check missingness, data types, units, duplicate keys, time gaps. Write findings to a new section in `audits/vN-data-qa.md`.
2. Validation Auditor runs [checklists/leakage-audit.md](../checklists/leakage-audit.md) grep on any existing `src/` code; document patterns found in `audits/vN-leakage.md`.
3. Compute sha256 hash of the full dataset and record in `runs/vN/data.sha256` for reproducibility gates.
4. If any data quality or leakage issue is found, file a new hypothesis or event into the appropriate playbook (open v(N+1) if blocking).

## Persona invocations
- **Validation Auditor** (primary): Run leakage audit and data QA. Output: `audits/vN-leakage.md` with Verdict [PASS | BLOCK].
- **Skeptic** (optional, if called on surprising data patterns): Review data structure and hypothesis of surprises.

## Exit gate
`audits/vN-leakage.md` Verdict=PASS AND data quality issues resolved or documented.

## Events that can abort this phase
- `leakage-found` (audit hits a leak pattern; mark affected runs and open v(N+1))
- `assumption-disproven` (data contradicts framing; update data-contract and open v(N+1))
