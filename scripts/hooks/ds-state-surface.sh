#!/usr/bin/env bash
# Hook: UserPromptSubmit
# Purpose: Surface current ds-workspace state on every user message so the
#          orchestrator always knows where it is without re-reading files.
#
# Install in ~/.claude/settings.json:
#   "hooks": {
#     "UserPromptSubmit": [
#       {
#         "matcher": "",
#         "command": "bash $SKILL/scripts/hooks/ds-state-surface.sh",
#         "description": "Surface ds-workspace phase + last journal entry"
#       }
#     ]
#   }
#
# Security: read-only. Does not modify any file. Outputs to stdout (injected
# into Claude's context as a system-reminder by the CC hook runner).

set -euo pipefail

WORKSPACE="${DS_WORKSPACE:-ds-workspace}"

# --- state.json ---
STATE_FILE="$WORKSPACE/state.json"
if [[ -f "$STATE_FILE" ]]; then
  PHASE=$(python3 -c "import json,sys; s=json.load(open('$STATE_FILE')); print(s.get('current_phase','?'))" 2>/dev/null || echo "?")
  VERSION=$(python3 -c "import json,sys; s=json.load(open('$STATE_FILE')); print(s.get('current_version','?'))" 2>/dev/null || echo "?")
  MODE=$(python3 -c "import json,sys; s=json.load(open('$STATE_FILE')); cm=s.get('competition_mode'); print('competition' if cm else 'daily' if cm is False else '?')" 2>/dev/null || echo "?")
  HOLDOUT=$(python3 -c "import json,sys; s=json.load(open('$STATE_FILE')); print(s.get('holdout_reads',0))" 2>/dev/null || echo "?")
  echo "=== DS-WORKSPACE STATE ==="
  echo "Phase: $PHASE | Version: v$VERSION | Mode: $MODE | Holdout reads: $HOLDOUT"
else
  echo "=== DS-WORKSPACE STATE ==="
  echo "(no state.json found — workspace not yet initialised)"
fi

# --- Last 8 lines of most recent step-journal ---
JOURNAL_FILE="$(ls -t "$WORKSPACE/step-journal/"*.md 2>/dev/null | head -1)"
if [[ -n "$JOURNAL_FILE" && -f "$JOURNAL_FILE" ]]; then
  echo "--- Last step-journal entry ---"
  tail -n 8 "$JOURNAL_FILE"
fi

# --- Active blockers from leaderboard ---
LB_FILE="$WORKSPACE/dashboard/data/leaderboard.json"
if [[ -f "$LB_FILE" ]]; then
  INVALIDATED=$(python3 -c "
import json, sys
lb = json.load(open('$LB_FILE'))
runs = lb.get('runs', [])
bad = [r['id'] for r in runs if r.get('status') == 'invalidated']
print('Invalidated runs: ' + ', '.join(bad) if bad else '')
" 2>/dev/null || echo "")
  if [[ -n "$INVALIDATED" ]]; then
    echo "--- Leaderboard alert ---"
    echo "$INVALIDATED"
  fi
fi
