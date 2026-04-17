---
name: ds
description: Start or resume the data-science-iteration loop on the current project.
---

# /ds

Invokes the `data-science-iteration` skill.

**First run:** if `ds-workspace/state.json` does not exist, run `/ds-init` first (or `python3 $SKILL/scripts/init_workspace.py`) to bootstrap the workspace, then resume here. `/ds` then asks the five framing questions (decision / grain+time / threshold / track / mode: competition or daily), dispatches Literature Scout (Lite, required in competition / recommended in daily), drafts `plans/v1.md`, and enters the DGP phase.

**Subsequent runs:** read `ds-workspace/state.json` and resume from `current_phase`. Do NOT re-ask framing questions unless `current_phase == "FRAME"` with unanswered fields. If `current_phase == "ABORTED"`, present the surrender summary and wait for `reset-surrender` or `force v+1 <reason>` — do not resume autonomously. See SKILL.md §"Entry protocol" for the full contract.

Arguments (optional):
- `status` — print current phase, blockers, and leaderboard top-3, then exit.
- `ship`   — open the ship-gate sequence.
- `abort`  — tear down without reading holdout; dashboard preserved.
- `force v+1 <reason>` — close current vN and open v(N+1) with <reason>.
- `dig <hypothesis>` — branch investigation within the current vN.

On invocation, read `SKILL.md` of `data-science-iteration` and follow its entry flow.
