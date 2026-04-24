#!/usr/bin/env bash
# Hook: Stop
# Purpose: At session end, run knowledge_lint on the workspace and surface
#          any warnings so the next session starts with visibility. Works
#          alongside ds-phase-check.sh (phase-level) by covering the
#          knowledge-base side.
#
# Install in ~/.claude/settings.json:
#   "hooks": {
#     "Stop": [
#       {
#         "command": "bash $SKILL/scripts/hooks/ds-session-digest.sh",
#         "description": "Knowledge-base digest at session end"
#       }
#     ]
#   }
#
# Security: read-only. Exits 0 always.

set -euo pipefail

WORKSPACE="${DS_WORKSPACE:-ds-workspace}"

[[ -d "$WORKSPACE" ]] || exit 0

# Resolve the skill root. Prefer the SKILL env var set by the hook runner;
# fall back to walking up from this script's location.
if [[ -n "${SKILL:-}" && -f "${SKILL}/scripts/knowledge_lint.py" ]]; then
  LINTER="${SKILL}/scripts/knowledge_lint.py"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LINTER="$(cd "$SCRIPT_DIR/../.." && pwd)/scripts/knowledge_lint.py"
fi

[[ -f "$LINTER" ]] || exit 0

OUTPUT=$(python3 "$LINTER" "$WORKSPACE" 2>/dev/null || true)

# Only surface when the linter found something. "GREEN" means no warnings.
if [[ -n "$OUTPUT" ]] && ! echo "$OUTPUT" | grep -q "GREEN"; then
  echo "=== KNOWLEDGE BASE DIGEST ==="
  echo "$OUTPUT"
  echo ""
  echo "Resume next session with /ds-kb for review or /ds-coach for direction."
fi

exit 0
