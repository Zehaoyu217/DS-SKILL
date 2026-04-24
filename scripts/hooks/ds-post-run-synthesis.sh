#!/usr/bin/env bash
# Hook: PostToolUse (matcher: "Bash")
# Purpose: After a tool call completes, nudge the orchestrator to produce
#          `audits/vN-model-synthesis.md` when the current version has
#          `audits/vN-model-diagnostics.md` but no synthesis yet. Targets
#          Iron Law #26 directly — keeps the loop from drifting into the
#          next run before distilling what the current one taught.
#
# Install in ~/.claude/settings.json:
#   "hooks": {
#     "PostToolUse": [
#       {
#         "matcher": "Bash",
#         "command": "bash $SKILL/scripts/hooks/ds-post-run-synthesis.sh",
#         "description": "Remind to write model-synthesis after training runs"
#       }
#     ]
#   }
#
# Security: read-only. Exits 0 always (advisory, not blocking). The matcher
# is broad (any Bash call) but the hook self-filters — it only emits a
# message when diagnostics are present without a synthesis.

set -euo pipefail

WORKSPACE="${DS_WORKSPACE:-ds-workspace}"
STATE_FILE="$WORKSPACE/state.json"

[[ -f "$STATE_FILE" ]] || exit 0

PHASE=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s.get('current_phase',''))" 2>/dev/null || echo "")
VERSION=$(python3 -c "import json; s=json.load(open('$STATE_FILE')); print(s.get('current_version','1'))" 2>/dev/null || echo "1")
V="v${VERSION}"

# Only act during phases where diagnostics/synthesis are expected.
case "$PHASE" in
  FEATURE_MODEL|VALIDATE) ;;
  *) exit 0 ;;
esac

DIAG="$WORKSPACE/audits/${V}-model-diagnostics.md"
SYNTH="$WORKSPACE/audits/${V}-model-synthesis.md"

if [[ -f "$DIAG" && ! -f "$SYNTH" ]]; then
  cat <<EOF
=== MODEL-AS-TEACHER NUDGE ===
${V}: model-diagnostics present but no model-synthesis yet.
Iron Law #26 requires audits/${V}-model-synthesis.md before VALIDATE exit.

Before starting the next run, distill this one:
  template  -> \$SKILL/templates/model-synthesis.md
  checklist -> \$SKILL/checklists/model-as-teacher.md
Then: /ds-kb apply-patches audits/${V}-model-synthesis.md
EOF
fi

# Secondary check: if synthesis exists but §6 Implications looks empty,
# surface the quality-bar warning. This catches the single-metric trap
# where a synthesis file was created to silence the gate but left hollow.
if [[ -f "$SYNTH" ]]; then
  EMPTY_SIX=$(python3 - "$SYNTH" <<'PYEOF' 2>/dev/null || echo "0"
import re, sys
text = open(sys.argv[1]).read()
m = re.search(r"(?:^|\n)## 6\. Implications(.*?)(?=\n## |\Z)", text, re.DOTALL)
if not m:
    print("1")
    sys.exit(0)
body = m.group(1)
bullets = [
    ln for ln in body.splitlines()
    if ln.strip().startswith("- ")
    and not ln.strip().startswith("- <")
    and "—" in ln
]
print("1" if not bullets else "0")
PYEOF
)
  if [[ "$EMPTY_SIX" == "1" ]]; then
    echo "=== MODEL-AS-TEACHER QUALITY NUDGE ==="
    echo "${V} synthesis §6 Implications has no concrete bullets."
    echo "Single-metric trap — name a variable, hypothesis, basis row, insight, or segment."
  fi
fi

exit 0
