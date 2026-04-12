---
name: ds
description: Start or resume the data-science-iteration loop on the current project.
---

# /ds

Invokes the `data-science-iteration` skill. On first run, asks the four framing
questions (decision / grain+time / threshold / track), creates `ds-workspace/`,
and starts the dashboard server. On subsequent runs in a project that already
has `ds-workspace/state.json`, resumes from the last phase.

Arguments (optional):
- `status` — print current phase, blockers, and leaderboard top-3, then exit.
- `ship`   — open the ship-gate sequence.
- `abort`  — tear down without reading holdout; dashboard preserved.
- `force v+1 <reason>` — close current vN and open v(N+1) with <reason>.
- `dig <hypothesis>` — branch investigation within the current vN.

On invocation, read `SKILL.md` of `data-science-iteration` and follow its entry flow.
