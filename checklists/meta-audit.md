# Meta-audit checklist (Iron Law #22 + #24)

Used by the Meta-Auditor subagent ([personas/meta-auditor.md](../personas/meta-auditor.md))
at trajectory checkpoints.

## When to run
- Every `autonomous.yaml.autonomy.require_meta_audit_every_n_versions` versions (default 10)
- Before `disproven/surrender-vN.md` emission (auto-defeat)
- Before auto-ship in autonomous mode
- Before any scope=`permanent` override of a non-core iron law
- On user command `/ds meta-audit`

## Preconditions
- ≥3 versions exist (no meta-audit possible on v1 or v2)
- `coverage.json` exists and is schema-valid
- `budget.json` exists

## Sections

### 1. Drift from pre-registration
- [ ] `plans/v1.md.pre_registration.primary_metric` == current `plans/vN.md` primary_metric OR every change has `trigger_refs`
- [ ] v1 `secondary_metrics[]` ⊆ current `secondary_metrics[]` (additions OK; removal requires override id)
- [ ] `success_threshold.target` unchanged OR change has rationale
- [ ] CV scheme unchanged OR covariate-shift event justifies change
- Verdict: PASS | BLOCK | WARN

### 2. Anti-Goodhart trajectory (Iron Law #23)
- [ ] For each declared secondary metric, compute values at v1, v{floor(N/2)}, vN
- [ ] Flag any metric whose value at vN is worse than at v1 by >2σ of that metric's
      cross-run std (use feature-baseline runs as reference if available)
- [ ] Flag any metric that monotone-degraded for ≥3 consecutive versions
- [ ] Cross-reference top-5 features: any feature that appears in top-5 at vN but
      was absent at v1 AND degrades a secondary metric requires explanation
- Verdict: PASS | BLOCK | WARN

### 3. Coverage map sanity (Iron Law #25)
- [ ] Every `pattern_area` with `exhausted: true` has either ≥3 `approaches_tried`
      OR a `ceiling_reason: intrinsic` with documented evidence
- [ ] No `priority: top` area has `approaches_tried == []`
- [ ] `remaining_leverage_estimate` > 0.5 on an `exhausted: true` area requires
      justification in `notes_ref`
- [ ] `ceiling_reason: approach-exhausted` count vs `feature-limited` count —
      skewed distributions (all one reason) suggest the orchestrator is pattern-
      matching rather than genuinely diagnosing
- Verdict: PASS | BLOCK | WARN

### 4. Budget audit (Iron Law #21)
- [ ] `budget.json.ledger` sum matches leaderboard run count × declared cost-per-run
- [ ] `remaining` on every envelope dimension: if any is <20% of initial, flag
- [ ] Wall-clock elapsed vs declared: if >80% of budget AND metric still below
      target, recommend re-scope or surrender-card
- [ ] Any ledger entries for runs not on the leaderboard (orphan spend) → BLOCK
- Verdict: PASS | BLOCK | WARN

### 5. Override inventory (Iron Law #24)
- [ ] Count overrides by scope: run / version / permanent
- [ ] Flag if `permanent` count ≥3 (systemic relaxation, not exception)
- [ ] Flag if any `expires_at` is past AND override id is still in `state.active_overrides`
- [ ] Any override of Iron Laws #1, #12, #16, #17, #20 or `law=budget` authorized by Council (not human)
      → CRITICAL BLOCK (core-law overrides must be human-gated even in autonomous mode).
      #16 and #20 additionally reject scope=`permanent` outright — any permanent-scope card for those laws is a CRITICAL BLOCK regardless of signers.
- [ ] For each permanent override: was the original risk rechecked at SHIP? If not, WARN
- Verdict: PASS | BLOCK | WARN

### 6. Trajectory diagnostics
- [ ] Top-5 feature stability across versions — compute Jaccard similarity between
      v(N-5) and vN top-5. Churn >0.5 = noise-chasing candidate
- [ ] Adversarial-validation AUC trend — rising AUC means we are *creating* drift
      (e.g., via features that encode version-index or leakage from updated labels)
- [ ] CV-to-holdout gap at internal-ship events: widening gap = overfit risk
- [ ] Learning rate: CV-mean points gained per version over last 3 versions
- [ ] Ship-rate: ships-attempted / ships-succeeded in last 10 versions
- Verdict: informational, surfaces concerns

### 7. Council quorum history
- [ ] Review all Council dispatches in last N versions
- [ ] Count 2/3 consensus vs 3/3 consensus vs quorum-failures
- [ ] If ≥2 quorum-failures in last 10 versions, recommend switching that decision
      class back to human-gated
- [ ] Any Council member whose verdict never dissents → Skeptic-variant diversity broken

### 8. Verdict composition

- **PASS**: no CRITICAL, ≤1 HIGH, ≤3 WARN
- **BLOCK**: any CRITICAL OR ≥2 HIGH
- **RECOMMEND SURRENDER**: even a PASS may recommend surrender-card if learning-rate
  has been <0.001 for ≥5 versions AND all top-priority pattern areas are exhausted
- **ESCALATE TO HUMAN**: any core-law override attempt, any quorum-failure-twice,
  any CRITICAL finding. Exits autonomous mode until human resumes.

## Output file

`ds-workspace/<meta_audit_dir>/vN-meta-audit.md` using the template in
[personas/meta-auditor.md](../personas/meta-auditor.md). `<meta_audit_dir>` is read
from `autonomous.yaml.logging.meta_audit_artifact_dir` (default `audits/meta/`).
