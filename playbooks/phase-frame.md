# Phase: FRAME

## Entry gate
Project has a `data/` directory OR user invoked `/ds`. `ds-workspace/` has been scaffolded.

## Purpose
Frame the problem. Produce: data-dictionary review, four answered framing questions, plan v1 draft, data contract, locked internal holdout with signature, CV scheme choice, Lite-mode literature memo, budget envelope (Iron Law #21), pre-registered anti-Goodhart secondary metrics (Iron Law #23), and seeded coverage map (Iron Law #25). Dual sign-off (Skeptic + Validation Auditor) on framing artifacts. This phase does NOT produce the DGP memo — that is the next phase (Iron Law #12).

## Steps (in order)
1. **Read what the organizer / user gave us.** Load the data dictionary, problem statement, metric definition, and (if competition) `sample_submission.csv` format. Write summary to `data-contract.md` §0 "organizer inputs".
2. **Ask four framing questions one at a time, waiting for user input between each:**
   - (1a) What decision does this model support? (grounds metric and success definition)
   - (1b) Data unit/grain and time structure? (grounds CV scheme options)
   - (1c) Hard success threshold? (grounds ship gate)
   - (1d) Track: notebook or script? (grounds code organization)
   - (1e) Mode? [competition/daily] — competition: full ceremony, one-shot submission (Iron Law #16). daily: lighter gates, faster iteration. See mode comparison table in [SKILL.md](../SKILL.md).
3. **Write `plans/v1.md`** using the plan template, including hypothesis list, kill criteria, AND a "Pre-registered decisions" section listing the CV scheme, primary metric, success threshold, model family shortlist, and any planned ablations. Pre-registration is what the ship-gate later diffs against.
4. **Write `data-contract.md`**: describe data sources, grain, time range, schema, assumptions, and data quality SLAs. Note any fields you already suspect are `at-label` or `post-label` (the full provenance audit happens in the DGP phase).
5. **Carve locked internal holdout.** Stratified random sample (size set by target volume/variance; time-aware if data has time structure); compute sha256; write `holdout/HOLDOUT_LOCK.txt` with hash, timestamp, and "DO NOT READ UNTIL INTERNAL SHIP" banner. In competition mode, note explicitly that this is an *internal* holdout distinct from the organizer's hidden test.
6. **Decide CV scheme** using [checklists/cv-scheme-decision.md](../checklists/cv-scheme-decision.md); document choice in `audits/v1-cv-scheme.md`. The chosen scheme must tentatively accommodate the shift axes the user already suspects; the adversarial-validation step in AUDIT will test and potentially reopen this.
7. **Dispatch Literature Scout in Lite mode** regardless of model novelty (Iron Law #7). Produce `literature/v1-memo.md` summarizing ≥5 prior-art sources on this problem class. This memo seeds the DGP memo §6 (priors) that follows.
8. **Declare the budget envelope (Iron Law #21).** Write `ds-workspace/budget.json` declaring `{compute_hours, wall_clock_days, api_cost_usd, max_versions, max_runs_per_version}`. Any dimension left null is "unlimited" and is discouraged in autonomous mode — the Skeptic flags null envelopes in step 10. Schema: [templates/budget.schema.json](../templates/budget.schema.json). In autonomous mode, values seed from `autonomous.yaml.budget`. Smoke-test via `python3 scripts/budget_check.py ds-workspace --check` (must exit 0).
9. **Pre-register anti-Goodhart secondary metrics (Iron Law #23).** In `plans/v1.md` §pre_registration, declare ≥2 `secondary_metrics` from [checklists/anti-goodhart.md](../checklists/anti-goodhart.md) (e.g., `calibration_ece`, `worst_segment_score`, `prediction_entropy`, `class_parity_gap`, `per_feature_stability`). Each secondary must include `{name, direction: min|max, max_degradation_sigma}`. These are the metrics the ship-gate checks degradation against and that `scripts/tracker_log.py` logs to the leaderboard `secondary_metrics` field on every run.
10. **Seed the coverage map (Iron Law #25).** `scripts/init_workspace.py` seeds `coverage.json` with the six ds-patterns pattern areas at init. At FRAME exit, adjust `priority` fields for each area based on the data-contract: areas obviously relevant to this problem move to `priority: top`; irrelevant ones move to `priority: low`. Leave `approaches_tried: []` and `last_tried_vN: 0` — they are populated by VALIDATE exits.
11. **Dispatch Skeptic + Validation Auditor in parallel.**

## Persona invocations
- **Skeptic** (parallel): Review `plans/v1.md` for concrete, falsifiable tests, explicit kill criteria, and pre-registration completeness (including the ≥2 anti-Goodhart secondaries). Flag any null dimension in `budget.json` and any `priority: top` pattern area without a rationale in `coverage.json.notes_ref`. Output: `audits/v1-skeptic.md` with Verdict [PASS | BLOCK].
- **Validation Auditor** (parallel): Review and sign `audits/v1-cv-scheme.md` confirming scheme is appropriate for grain/time structure. Output: signed `audits/v1-cv-scheme.md`.
- **Literature Scout** (parallel, Lite mode): Produce `literature/v1-memo.md`.

## Exit gate
All of:
- `audits/v1-skeptic.md` Verdict=PASS
- `audits/v1-cv-scheme.md` signed by Validation Auditor
- `literature/v1-memo.md` present
- `data-contract.md` complete
- `holdout/HOLDOUT_LOCK.txt` written
- `budget.json` present with schema validation passing and `budget_check.py --check` exit 0 (Iron Law #21)
- `plans/v1.md` §pre_registration.secondary_metrics has ≥2 entries (Iron Law #23)
- `coverage.json` present with schema validation passing and priorities set (Iron Law #25)

## Events that can abort this phase
- `leakage-found` (on initial data peek; halt and file remediation into v2)
- `assumption-disproven` (if framing assumption falsified during holdout carve; update data-contract and open v2)
