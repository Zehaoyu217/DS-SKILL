---
# Machine-readable metadata (consumed by scripts/consistency_lint.py).
id: learnings-v{N}
version: {N}
parent_plan: plan-v{N}
status: open          # open → closed when VALIDATE exits for vN
phase_exits_recorded: []   # list of phase names appended so far: DATA_PREP | EDA | FEATURE_MODEL | VALIDATE
feeds_dgp_section: 6       # summary block is primary input for dgp-memo §6 in v(N+1)
created_at: YYYY-MM-DDTHH:MM:SSZ
last_updated_at: YYYY-MM-DDTHH:MM:SSZ
---

# Learnings v{N}

Within-version learning log. Distinct from:
- `step-journal/v{N}.md` — append-only chain-of-thought (reasoning traces, raw decisions)
- `ds-workspace/lessons.md` — promoted cross-version learnings (global, Skeptic-signed, persistent)

This file captures **belief updates** per phase exit: what we expected vs. what we observed, and what that means for the current plan and the next version. It is the primary input for `dgp-memo.md §6` in v(N+1) and for the FRAME framing questions of that version.

Entries are **append-only within the version**. Never edit a prior entry; add a new one that supersedes it with `supersedes: entry-NNN`.

---

## DATA_PREP exit

*(Append this block when DATA_PREP exits.)*

### Entry L-{N}-001
- **When:** <ISO timestamp>
- **Phase:** DATA_PREP
- **What we expected:**
  <Pointer to plan hypothesis or DGP prediction (e.g., "H-v{N}-02 assumed feature X was complete; DGP §2 flagged it as at-label")>
- **What we observed:**
  <Concrete artifact, e.g., "`audits/v{N}-data-prep.md §2`: col `age` is 18% missing, MNAR by cohort year — not MCAR as assumed">
- **Belief update:**
  - Direction: positive | negative | null  *(did this confirm, contradict, or not touch a prior belief?)*
  - Magnitude: large | medium | small | negligible
  - <2–4 sentences summarizing what changed in our mental model>
- **Feed-forward action:**
  - [ ] Feed DGP §6 of v(N+1): <what prior to update; cite this entry>
  - [ ] Revise hypothesis: <H-id> → <new statement>; trigger: append to `plans/v{N}-updates.md` rev-NNN
  - [ ] Refine brainstorm contingency: <brainstorm file, alternative id>
  - [ ] None — observation within expected range; no action

*(Add more entries as surprises arise within DATA_PREP or at its exit.)*

---

## EDA exit

*(Append this block when EDA exits.)*

### Entry L-{N}-0NN
- **When:** <ISO timestamp>
- **Phase:** EDA
- **What we expected:**
  <Pre-registered hypothesis or DGP prediction being tested here>
- **What we observed:**
  <Artifact + finding, e.g., "`runs/v{N}/plots/feature-Y-distribution.png`: strong bimodality — not visible in summary stats at DATA_PREP">
- **Belief update:**
  - Direction: positive | negative | null
  - Magnitude: large | medium | small | negligible
  - <2–4 sentences>
- **Feed-forward action:**
  - [ ] Feed DGP §6 of v(N+1): <cite entry>
  - [ ] Hypothesis refined: <H-id>; trigger: append plan-updates rev-NNN
  - [ ] New hypothesis added: <H-id>; kill criterion: <statement>
  - [ ] None

---

## FEATURE_MODEL exit

*(Append this block when FEATURE_MODEL exits.)*

### Entry L-{N}-0NN
- **When:** <ISO timestamp>
- **Phase:** FEATURE_MODEL
- **What we expected:**
  <Prediction from brainstorm or DGP §7a (e.g., "brainstorm-FEATURE_MODEL A1 predicted GBM > linear by ~5% AUC given non-linear target")>
- **What we observed:**
  <Leaderboard outcome + ablation, e.g., "`runs/v{N}/metrics.json`: GBM cv_mean=0.821 vs linear cv_mean=0.799 — lift matches prediction but feature_lift_vs_feature_baseline was negligible (0.003)">
- **Belief update:**
  - Direction: positive | negative | null
  - Magnitude: large | medium | small | negligible
  - <2–4 sentences — separately characterize model-family lift vs. feature-engineering lift>
- **Feed-forward action:**
  - [ ] Feed DGP §6 of v(N+1): feature-engineering approach underperformed — investigate different representations in v(N+1)
  - [ ] Emit disproven-card for dropped candidate: `disproven/v{N}-dNNN.md`
  - [ ] Candidate for promotion to `lessons.md`: <what and why>
  - [ ] None

*(Record one entry per major candidate or surprising ablation result, not one global entry.)*

---

## VALIDATE exit (closes the log)

*(Append this block when VALIDATE exits. Set `status: closed` in frontmatter.)*

### Entry L-{N}-0NN
- **When:** <ISO timestamp>
- **Phase:** VALIDATE
- **Expanded interval vs. holdout:**
  - `predicted_interval`: <cv_mean ± …> (from `audits/v{N}-ship-gate.md`)
  - Holdout metric (if internal-ship already run): <value> — within interval? yes | no
  - If no: fire `cv-holdout-drift`; do NOT close this log as "clean"
- **Uncertainty observations:**
  <Did `seed_std / lift_vs_baseline` look stable? Did `cv_ci95` narrow or widen vs. v(N-1)? Cite `runs/v{N}/metrics.json`>
- **Belief update:**
  - Direction: positive | negative | null
  - Magnitude: large | medium | small | negligible
  - <What does the gap behavior tell us about the DGP distribution-shift axes?>
- **Feed-forward action:**
  - [ ] Feed DGP §6 of v(N+1): <what to update in the DGP memo for the next version>
  - [ ] Update plan hypothesis status: <H-id> → RESOLVED | DISPROVEN
  - [ ] Candidate for promotion to `lessons.md`: <what and why>
  - [ ] None

## Summary at close

*(Written at VALIDATE exit when status is set to closed. This paragraph is the primary input for v(N+1) FRAME and DGP §6.)*

- **Biggest belief updates this version (top 3):** <cite entry ids>
- **What to carry forward to DGP §6 in v(N+1):**
  <3–5 concrete statements about priors updated by this version's evidence, each citable to an entry above>
- **What to carry forward to `plans/v{N+1}.md`:**
  <Open questions, unresolved hypotheses, candidates worth re-exploring with different configurations>
- **What to retire:**
  <Hypotheses or approaches confirmed dead; cite disproven-cards>

---

## Usage rules

1. **Append-only.** Do not edit prior entries. To retract or refine one, add a new entry with `supersedes: L-{N}-0NN`.
2. **Every entry must cite a concrete artifact.** Vague observations ("things went poorly in EDA") are not useful feed-forward. Cite the file and section.
3. **Belief direction is required.** "Positive" means the observation confirmed a prior belief or raised our confidence in the plan. "Negative" means it contradicted or lowered our confidence. "Null" means no existing belief was touched.
4. **Feed-forward is required.** At minimum, check "None" with a one-line justification. Blank feed-forward cells fail the exit gate.
5. **Close at VALIDATE exit.** Set `status: closed` in frontmatter and write the Summary at close block. After that, learnings flow into `learnings-v{N+1}.md` in the next version.
6. **Summary at close is the DGP §6 input.** When drafting DGP memo for v(N+1), read this summary first. "Priors from literature / domain" should cite entries from this file, not just literature.
