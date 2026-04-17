---
# Machine-readable plan-update metadata (consumed by scripts/consistency_lint.py).
id: plan-updates-v{N}
version: {N}
parent_plan: plan-v{N}
revisions: []                        # list of revision ids; populated below; each revision must reference a concrete trigger artifact
status: open | closed                # "closed" when VALIDATE has exited for vN; after that, updates flow into plan-v{N+1} instead
created_at: YYYY-MM-DDTHH:MM:SSZ
last_updated_at: YYYY-MM-DDTHH:MM:SSZ
---

# Plan Updates — v{N}

Progressive log of how `plans/v{N}.md` evolved *within* this version, in response to artifacts produced by DATA_PREP, EDA, FEATURE_MODEL, and VALIDATE. The original plan is never rewritten in place — every change is appended here as a dated revision with a triggering artifact. This creates the thinking trail: what was the plan, what did we learn, how did the plan change, and why.

If a learning is large enough that it invalidates the plan's framing or primary metric, it does NOT belong here — it triggers `assumption-disproven` and opens v(N+1). This log is for refinements within an otherwise-valid plan.

## Revisions

Append a new revision block at each of the following milestones (at minimum):

- **DATA_PREP exit** — surprises from schema / missing / outlier / join analysis that change which hypotheses are testable or how features should be constructed
- **EDA exit** — new hypotheses added by Explorer; existing hypotheses revised or retired based on observed patterns
- **FEATURE_MODEL exit** — which candidates / features / tuning strategies were tried, which worked, which were dropped, what the winning configuration is
- **VALIDATE exit** — whether the uncertainty / holdout behavior matches what the plan predicted; any surprises that change the shipping interval

Additional revisions may be appended any time a brainstorm is finalized or a non-trivial decision is made.

### Revision rev-001
- **When:** <ISO timestamp>
- **Milestone:** DATA_PREP exit | EDA exit | FEATURE_MODEL exit | VALIDATE exit | mid-phase
- **Triggered by:** <artifact path, e.g., `audits/v{N}-data-prep.md §4` or `runs/v{N}/brainstorm-models.md`>
- **What changed in the plan:**
  - Hypothesis `H-v{N}-XX` status → `<new status>` (was `<old status>`)
  - Hypothesis `H-v{N}-YY` refined: <old statement> → <new statement> (rationale below)
  - New hypothesis added: `H-v{N}-ZZ` — <statement, kill criterion>
  - Pre-registered decision `<key>`: <old value> → <new value> (rationale below)
  - Stop rule added: <what new condition ends this iteration>
- **Why (rationale):**
  <2–5 sentences. Must cite the triggering artifact concretely — "EDA plot X revealed bimodality in feature Y, so hypothesis H-v{N}-02 is refined to test each mode separately."  Hand-wavy rationale ("seemed better") is flagged by the consistency linter.>
- **Consequences:**
  - Downstream phases affected: <list>
  - New artifacts needed: <list, e.g., "feature-brainstorm for bimodal split" → `runs/v{N}/brainstorm-features-bimodal.md`>
  - Supersedes: <prior revision id, if this reverses an earlier decision>

### Revision rev-002
(same structure)

### Revision rev-NNN
...

## Summary at close (written at VALIDATE exit)

Once VALIDATE exits for vN, append the following summary block. This is the single paragraph that the next iteration's FRAME phase reads first when constructing `plans/v{N+1}.md`.

- **Plan as executed (final):**
  - Hypotheses resolved: <count> → findings, <count> → disproven-cards, <count> unresolved (should be 0 by Iron Law #6)
  - Pre-registered decisions changed during execution: <count>; all rationale captured above
  - Winning configuration: <model family, feature set, tuning strategy; cite leaderboard run id>
- **Biggest lessons for v{N+1}:** <3–5 bullets of what to carry forward>
- **Open questions deferred to v{N+1}:** <list>

---

## Usage rules

1. **No rewriting `plans/v{N}.md`.** Once the plan is signed at FRAME exit, it is frozen. Changes are appended here as revisions. This preserves the thinking trail and prevents silent plan drift (which the consistency linter treats as a governance failure).
2. **Every revision must cite a concrete triggering artifact.** "Based on what we saw in EDA" is not enough; "based on `runs/v{N}/plots/feature-Y-distribution.png` showing bimodality" is required.
3. **Append-only within vN.** Revisions are not edited after they are written, only new ones are appended. To reverse a revision, add a new revision that supersedes it (set `supersedes: rev-XXX` in its body) with rationale.
4. **Close the log at VALIDATE exit.** Status transitions to `closed`; the summary block is written. After that, further learnings flow into `plans/v{N+1}.md` (via FRAME phase) rather than into this log.
5. **Three-revision minimum for non-trivial iterations.** A vN that produced zero plan-updates either (a) had a perfect plan — very rare, flag for human review, or (b) did not document learning honestly. The consistency linter warns on vN with fewer than 3 revisions unless `plans/v{N}.md` was explicitly marked `exploratory: false` at FRAME.
