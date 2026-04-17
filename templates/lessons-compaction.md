---
kind: lessons-compaction
vN_window: [v<start>, v<end>]
compacted_at: <ISO-8601>
input_file: lessons.md
input_size_lines: <int>
output_file: lessons.md
output_size_lines: <int>
archived_as: lessons-v<end>.md.archive
promoted_to_global: <count>
compactor: orchestrator-auto | user-invoked
---

# Lessons compaction v<start>..v<end>

This is the audit artifact for a lessons-compaction pass (Iron Law #25 scaling
guidance + SKILL.md rolling-knowledge philosophy). The *input* `lessons.md` has been
archived; the new `lessons.md` is the compacted result.

## Compaction rules

1. **Deduplicate**: identical or near-identical lessons from different versions are
   merged. Preserve the earliest `first_observed_vN` and all `confirming_vN` refs.
2. **Generalize**: lessons that apply to multiple pattern areas are promoted to a
   top-level "Cross-cutting" section. Project-local lessons stay in per-area sections.
3. **Promote durable lessons**: any lesson that has been confirmed across ≥3 versions
   with ≥2 seeds each AND has received Skeptic + Statistician sign-off is promoted to
   `~/.claude/skills/ds-learnings/YYYY-MM-DD-<project>-<slug>.md`. Update
   `promoted_to_global` count above and list the slugs in §Promotions.
4. **Drop stale**: lessons older than `v(current - 50)` that were never confirmed in
   a later version are dropped — they represent speculation that didn't survive.
   Note count in §Dropped.
5. **Preserve structure**: keep the existing `## Data quality / ## Feature engineering
   / ## Model selection / ...` sections; do not introduce new top-level headings
   without an accompanying coverage.json pattern area.

## Cadence

Auto-triggered at `v{10, 50, 100, 500, 1000, ...}` when the orchestrator passes
VALIDATE exit and `len(lessons.md.splitlines()) > 200 × compaction_count`. Also
triggered manually via `/ds compact-lessons`.

In autonomous mode, Meta-Auditor reviews the compaction diff before the archive is
written — any lesson marked CRITICAL for a future decision that was accidentally
dropped will be flagged.

## Promotions

List the lessons promoted to `ds-learnings/` in this pass:

- `<slug>`: <one-line summary>

## Dropped

List lessons dropped (with reasons):

- `<quote>` — reason: never confirmed after v<N>, contradicted by <finding-id>, etc.

## Verification

- [ ] `lessons.md` line count reduced
- [ ] All durable lessons still resolvable via finding-ids / disproven-ids
- [ ] Archived copy exists at `lessons-v<end>.md.archive`
- [ ] `consistency_lint.py` returns 0 after compaction (no broken refs)
- [ ] Meta-Auditor sign-off (autonomous mode only)
