# ds-* hooks for Claude Code

Shell-script hooks that surface workspace state to the orchestrator. Each
script is self-contained, read-only, and exits 0 — none of them block
tool calls. They are wired in `~/.claude/settings.json`; the individual
script headers contain their install snippets.

## Available hooks

| Script | Event | One-line purpose |
|---|---|---|
| `ds-state-surface.sh` | UserPromptSubmit | Shows current phase, version, mode, holdout reads, last step-journal entry, invalidated runs. |
| `ds-stale-basis-check.sh` | UserPromptSubmit | Warns when last N runs share the same feature basis + model family with no material lift (laziness detector). |
| `ds-phase-check.sh` | Stop | Warns if the current phase's primary exit-gate artifact is missing. |
| `ds-session-digest.sh` | Stop | Runs `knowledge_lint.py` and surfaces warnings (section staleness, unexplored variables, unconsumed synthesis patches). |
| `ds-post-run-synthesis.sh` | PostToolUse (Bash) | Nudges to produce `audits/vN-model-synthesis.md` when diagnostics exist without synthesis (Iron Law #26). Also catches empty §6 Implications. |

## Recommended install order

All five can run in parallel. Suggested starting configuration in
`~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "matcher": "", "command": "bash $SKILL/scripts/hooks/ds-state-surface.sh" },
      { "matcher": "", "command": "bash $SKILL/scripts/hooks/ds-stale-basis-check.sh" }
    ],
    "PostToolUse": [
      { "matcher": "Bash", "command": "bash $SKILL/scripts/hooks/ds-post-run-synthesis.sh" }
    ],
    "Stop": [
      { "command": "bash $SKILL/scripts/hooks/ds-phase-check.sh" },
      { "command": "bash $SKILL/scripts/hooks/ds-session-digest.sh" }
    ]
  }
}
```

`$SKILL` should resolve to the installed path of this skill (typically
`~/.claude/skills/data-science-iteration`).

## Tunables

Environment variables honoured by one or more hooks:

| Variable | Default | Used by | Purpose |
|---|---|---|---|
| `DS_WORKSPACE` | `ds-workspace` | all | Path to the workspace directory (relative to the cwd when the hook fires). |
| `DS_STALE_WINDOW` | `6` | `ds-stale-basis-check.sh` | Number of recent leaderboard runs considered. |
| `DS_STALE_LIFT` | `0.001` | `ds-stale-basis-check.sh` | Lift below which the window is judged stalled. |

## Safety invariants

- All hooks are read-only. None modify any file in the workspace.
- All hooks exit 0, so they never block Claude Code.
- Each hook self-filters: if the conditions it cares about are absent
  (no `state.json`, no `knowledge-base.md`, no leaderboard), it exits
  silently.
- Output goes to stdout, which Claude Code injects into the next context
  window as a system-reminder.
