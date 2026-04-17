# Lessons Learned — Rolling

> Consolidated, human-readable view of what we've learned across all versions in this project.
> Auto-appended by MERGE and SHIP phases from promoted `disproven/*.md` and `findings/*.md` with `generalizability: promotable`.
> `scripts/consistency_lint.py` flags lesson entries that later get contradicted by new findings (`supersedes` chain).

Structure is append-only per version. Never rewrite history; if a later version invalidates a prior lesson, add a new entry with `supersedes:` rather than editing the old one.

---

## v1

### L-v1-001 — <short slug>
- **Source:** findings/v1-fNNN.md | disproven/v1-dNNN.md
- **Claim / lesson:** <1–3 sentences>
- **Subject:** <feature | model | pipeline | data-subset>
- **Direction:** positive | negative | neutral | mixed
- **Evidence summary:** <metric + CI + n_seeds>
- **Generalizability:** project-local | promotable
- **DGP refs:** [P-001, P-003]
- **Supersedes:** []
- **Superseded by:** null
- **Promoted to ds-learnings:** yes | no

(more v1 lessons…)

---

## v2

### L-v2-001 — <short slug>
(same structure)

---

<!-- subsequent versions appended below -->
