# /ds-kb — Knowledge Base

Open, view, or propose edits to the curated knowledge base for this
data-science project. The knowledge base (`ds-workspace/knowledge-base.md`)
is the single linted view of what we know about the dataset and the
problem — distilled from `findings/`, `disproven/`, `step-journal/`, and
model diagnostics.

## Usage

### `/ds-kb` — show state

Read `ds-workspace/knowledge-base.md` and report (do NOT rewrite):

- Each section's `last_reviewed` vs `state.current_version`.
- Variables in §2 with `explored: []` (grouped by `in_feature_basis: true`
  first — those are the highest-priority gaps).
- DGP hypotheses in §3 with `status: pending` and `last_checked` older than
  3 versions.
- Segments in §6 with `trend_last_k_versions: flat | regressing` for ≥3
  versions.
- Open questions in §8 older than 5 versions.
- If `scripts/knowledge_lint.py` exists, run it and append its output.
  Otherwise, perform the above checks manually.

Output is a compact status report; no file writes.

### `/ds-kb init`

If `ds-workspace/knowledge-base.md` does not exist:

1. Copy `$SKILL/templates/knowledge-base.md` to
   `ds-workspace/knowledge-base.md`.
2. Fill §1 (Dataset profile) from `data-contract.md` and `state.json` where
   possible (row counts, target definition, joins).
3. Seed §2 (Variable catalog) with every column name from the data
   contract, each with `explored: []` and `in_feature_basis: false`. This
   is intentional — it makes the unexplored set visible from day one.
4. Leave §3–§8 templated (placeholders, no fake entries).
5. Set the top-of-file `last_reviewed: v<current>` stamps on every section
   to the current version.

### `/ds-kb update <section>`

Propose an edit to one section. Valid section keys:
`profile`, `variables`, `hypotheses`, `basis`, `insights`, `segments`,
`failure-modes`, `open-questions`.

Workflow:

1. Read the current section.
2. Draft the change (append, modify, or close item).
3. Update the section's `last_reviewed` to `state.current_version` only if
   the change is material (new variable explored, hypothesis status
   changed, new insight added). Cosmetic edits leave the stamp unchanged.
4. Show the diff to the user and apply on confirmation.

### `/ds-kb apply-patches <audit-file>`

Apply a `## Proposed KB updates` or `## Proposed KB patches` block from
any audit file as edits to `knowledge-base.md`. Each proposed patch is
shown to the user with its target section before being applied; the user
may accept, skip, or modify each patch individually.

Common sources:
- `audits/vN-research-lead.md` — cross-version coach patches.
- `audits/vN-model-synthesis.md` — per-version synthesis patches
  (Iron Law #26, §7).
- any other persona audit that proposes a patch block.

### `/ds-kb apply-coach <vN>`

Shortcut for `/ds-kb apply-patches audits/vN-research-lead.md`. Kept for
ergonomics; the underlying mechanism is the generic patch applier.

### `/ds-kb lint`

Run `python3 $SKILL/scripts/knowledge_lint.py ds-workspace` and show the
result. Until the linter ships, this falls back to the manual checks
performed by `/ds-kb` (show state).

## Notes

- **Single-writer rule:** only the orchestrator writes to
  `knowledge-base.md`. Other personas (Research Lead, Explorer, Skeptic)
  propose updates through their audit artifacts; the orchestrator applies
  them here via `/ds-kb update` or `/ds-kb apply-coach`.
- **Lint is warning-only.** KB staleness or gaps never block a phase
  transition. The KB is a forward-pushing tool, not a gate.
- **Append-only sources remain authoritative.** `findings/`, `disproven/`,
  and `step-journal/` are the raw logs; the KB is the curated view
  distilled from them. If the KB and the logs disagree, trust the logs —
  and update the KB.
- **Version stamps matter.** `last_reviewed` is what the Research Lead
  reads to decide whether a section needs attention. Update it truthfully.
