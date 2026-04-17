# Event: eval-harness-tampered

## Trigger

`scripts/hash_eval_harness.py <ds-workspace> --check` exits non-zero at any phase gate after AUDIT exit. This means the sha256 hash of `src/evaluation/` recorded at AUDIT exit no longer matches the current content.

## Immediate response

1. **Freeze all modeling work** — do not log new runs, do not promote provisional entries, do not continue any current phase step.
2. Dispatch **Validation Auditor** as an independent subagent to diff `src/evaluation/` against the last-known-clean commit and classify the change:
   - **Unintentional drift** (refactor, formatting, accidental edit): proceed to remediation path A.
   - **Intentional improvement** (bug fix, metric correction, dataset update): proceed to remediation path B.
   - **Adversarial or unexplained** (unknown changes, no commit trail): escalate to user immediately; do not auto-remediate.
3. Dispatch **Skeptic** as an independent subagent to assess whether any run logged since AUDIT exit may have benefited from the change (i.e., whether prior results are now incomparable).

## Remediation path A — unintentional drift

1. Revert the accidental change to restore the hash recorded in `audits/vN-eval-harness-lock.json`.
2. Confirm `hash_eval_harness.py --check` exits 0.
3. Document the incident in `step-journal/vN.md` with a `harness-tampered` event block.
4. No runs need to be invalidated (eval code was not intentionally changed).
5. Resume the interrupted phase.

## Remediation path B — intentional improvement

If the eval harness is legitimately improved (bug fix, better metric implementation, dataset boundary correction), the change is valid but **breaks comparability** with prior runs. Required steps:

1. **User must explicitly invoke the override command:**
   ```
   override eval-harness <reason>
   ```
   Without this command, the gate remains blocked regardless of how legitimate the change is.
2. The override command triggers:
   a. `hash_eval_harness.py <ds-workspace> --update` — recomputes and writes new hash to `audits/vN-eval-harness-lock.json`.
   b. All runs from before the change are marked `status: "invalidated"` with `invalidation_reason: "eval-harness-changed"` in `leaderboard.json`.
   c. A new leaderboard section (`_eval_epoch` field on each run) distinguishes runs pre/post change so the dashboard renders the break clearly.
3. Write the override artifact at `ds-workspace/overrides/vN-override-eval-harness.md` using [templates/override-card.md](../templates/override-card.md) with `law: eval-harness`, `scope: run|version` (permanent is not permitted for this law — each harness change is a bounded event), and `affected_runs: [<list of run ids marked invalidated>]`. The `reason` / `expected_risk` / `mitigation` fields capture what changed, why, and how comparability is preserved. Signed by user (`signed_by: [user]`) in interactive mode or by Council quorum in autonomous mode.
4. A fresh **model baseline run** and **feature baseline run** must be re-executed under the new harness before non-baseline runs can be promoted.

## Required artifacts before gate re-opens

- `audits/vN-eval-harness-lock.json` with updated hash (path B) OR restored original hash (path A).
- `step-journal/vN.md` event block for the incident.
- (Path B only) `overrides/vN-override-eval-harness.md` using `templates/override-card.md` — `signed_by` list MUST include the authorising signer (user or Council quorum). `consistency_lint.py` canonicalises `law: eval-harness` (slug) and `law: "20"` (numeric) to the same id and rejects any `scope=permanent` outright via `LAWS_REJECT_PERMANENT` — use `scope=run` with a re-lock plan.
- (Path B only) New baseline and feature-baseline runs on leaderboard under the new harness.

## Resolution criteria

`hash_eval_harness.py <ds-workspace> --check` exits 0 AND either (A) the original hash matches current content, OR (B) an override record exists and all pre-change runs are marked invalidated.

## Events this can chain into

- `suspicious-lift` — if the Skeptic review finds that invalidated runs showed anomalous lift patterns, fire the event for post-hoc audit.
- `leakage-found` — if the harness diff reveals a leakage-adjacent change (e.g., label column visible in evaluation code), treat as leakage-found and follow that playbook.

## Resume phase
- **Path A (restore):** resume at `state.current_phase` (unchanged). No runs invalidated, no baselines to re-run.
- **Path B (override + re-lock):** resume at `state.current_phase`, but FEATURE_MODEL may not promote non-baseline runs until fresh model-baseline AND feature-baseline runs are logged under the new harness (reflected in leaderboard with the new `_eval_epoch`).
