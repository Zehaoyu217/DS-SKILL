#!/usr/bin/env bash
# Hook: Stop
# Purpose: Before Claude Code stops, check that the current phase's primary
#          exit-gate artifact exists. Prints a warning (non-blocking) if the
#          gate is not yet satisfied, so the orchestrator doesn't silently
#          leave a phase in a half-finished state.
#
# Install in ~/.claude/settings.json:
#   "hooks": {
#     "Stop": [
#       {
#         "command": "bash $SKILL/scripts/hooks/ds-phase-check.sh",
#         "description": "Warn if current phase exit gate is not satisfied"
#       }
#     ]
#   }
#
# Security: read-only. Does not modify any file. Exit 0 always (warning, not
# block) — we never want the Stop hook to prevent Claude from stopping.

set -euo pipefail

WORKSPACE="${DS_WORKSPACE:-ds-workspace}"
STATE_FILE="$WORKSPACE/state.json"

if [[ ! -f "$STATE_FILE" ]]; then
  exit 0  # no workspace, nothing to check
fi

PHASE=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s.get('current_phase',''))" 2>/dev/null || echo "")
VERSION=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s.get('current_version','1'))" 2>/dev/null || echo "1")
V="v${VERSION}"

check_file() {
  local label="$1"
  local path="$2"
  if [[ ! -f "$path" ]]; then
    echo "  MISSING: $label ($path)"
    return 1
  fi
  return 0
}

MISSING=0

case "$PHASE" in
  FRAME)
    check_file "CV scheme audit"   "$WORKSPACE/audits/${V}-cv-scheme.md" || MISSING=1
    ;;
  DGP)
    check_file "DGP memo"          "$WORKSPACE/dgp-memo.md"              || MISSING=1
    ;;
  AUDIT)
    check_file "Adversarial audit" "$WORKSPACE/audits/${V}-adversarial.md" || MISSING=1
    ;;
  DATA_PREP)
    check_file "Data-prep brainstorm" "$WORKSPACE/runs/${V}/brainstorm-${V}-DATA_PREP.md" || MISSING=1
    ;;
  EDA)
    check_file "Explorer EDA audit" "$WORKSPACE/audits/${V}-explorer.md"  || MISSING=1
    ;;
  FEATURE_MODEL)
    check_file "Model brainstorm (Skeptic-signed)" "$WORKSPACE/runs/${V}/brainstorm-${V}-FEATURE_MODEL.md" || MISSING=1
    check_file "Leaderboard"      "$WORKSPACE/dashboard/data/leaderboard.json" || MISSING=1
    ;;
  VALIDATE)
    check_file "Learnings (closed)" "$WORKSPACE/runs/${V}/learnings.md"  || MISSING=1
    ;;
  FINDINGS)
    check_file "Findings dir"     "$WORKSPACE/findings"                   || MISSING=1
    ;;
  SHIP)
    check_file "Ship-gate checklist" "$WORKSPACE/audits/${V}-ship-gate.md" || MISSING=1
    ;;
esac

if [[ "$MISSING" -eq 1 ]]; then
  echo ""
  echo "DS-PHASE-CHECK WARNING: phase=$PHASE exit gate not yet satisfied."
  echo "Resume this session to complete the gate before the next session."
fi

exit 0  # always exit 0 — this is advisory only
