# Phase: FRAME

## Entry gate
Project has a `data/` directory OR user invoked `/ds`. `ds-workspace/` has been scaffolded.

## Purpose
Frame the problem by running four structured questions that ground the decision, data structure, success threshold, and tracking method. Output: plan v1 draft, data contract, locked holdout with signature, CV scheme choice, and dual sign-off (Skeptic + Validation Auditor) on all framing artifacts.

## Steps (in order)
1. Ask four framing questions one at a time, waiting for user input between each:
   - (1a) What decision does this model support? (grounds metric and success definition)
   - (1b) Data unit/grain and time structure? (grounds CV scheme options)
   - (1c) Hard success threshold? (grounds ship gate)
   - (1d) Track: notebook or script? (grounds code organization)
2. Write `plans/v1.md` using the plan template, including hypothesis list and kill criteria.
3. Write `data-contract.md`: describe data sources, grain, time range, schema, assumptions, and data quality SLAs.
4. Carve locked holdout: stratified random sample (size set by target volume/variance); compute sha256 hash; write `holdout/HOLDOUT_LOCK.txt` with hash, timestamp, and "DO NOT READ UNTIL SHIP" banner.
5. Decide CV scheme using [checklists/cv-scheme-decision.md](../checklists/cv-scheme-decision.md); document choice in `audits/v1-cv-scheme.md`.
6. Invoke Skeptic and Validation Auditor in parallel: Skeptic reviews plan hypothesis clarity and kill criteria; Validation Auditor signs off on CV scheme choice.

## Persona invocations
- **Skeptic** (parallel): Review `plans/v1.md` for concrete, falsifiable tests and explicit kill criteria. Output: `audits/v1-skeptic.md` with Verdict [PASS | BLOCK].
- **Validation Auditor** (parallel): Review and sign `audits/v1-cv-scheme.md` confirming scheme is appropriate for grain/time structure. Output: signed `audits/v1-cv-scheme.md`.

## Exit gate
`audits/v1-skeptic.md` Verdict=PASS AND `audits/v1-cv-scheme.md` signed by Validation Auditor.

## Events that can abort this phase
- `leakage-found` (on initial data peek; halt and file remediation into v2)
- `assumption-disproven` (if framing assumption falsified during holdout carve; update data-contract and open v2)
