#!/usr/bin/env bash
# Hook: UserPromptSubmit
# Purpose: Detect when the project has been iterating on the same feature
#          basis and model family for too long with no material lift —
#          the frozen-basis laziness failure mode (projects have been seen
#          running 100+ versions on a basis that was never revisited).
#          Emits a nudge to consider a basis rotation or pattern-area
#          pivot before another same-family run is started.
#
# Install in ~/.claude/settings.json:
#   "hooks": {
#     "UserPromptSubmit": [
#       {
#         "matcher": "",
#         "command": "bash $SKILL/scripts/hooks/ds-stale-basis-check.sh",
#         "description": "Warn when feature basis + model family have stalled"
#       }
#     ]
#   }
#
# Tunables (env overrides):
#   DS_STALE_WINDOW  — how many recent runs to consider (default 6)
#   DS_STALE_LIFT    — lift threshold below which we call it stalled
#                      (default 0.001, unit: primary_metric)
#
# Security: read-only. Exits 0 always (advisory, not blocking).

set -euo pipefail

WORKSPACE="${DS_WORKSPACE:-ds-workspace}"
LB_FILE="$WORKSPACE/dashboard/data/leaderboard.json"
WINDOW="${DS_STALE_WINDOW:-6}"
LIFT="${DS_STALE_LIFT:-0.001}"

[[ -f "$LB_FILE" ]] || exit 0

python3 - "$LB_FILE" "$WINDOW" "$LIFT" <<'PYEOF' 2>/dev/null || true
import json
import sys

if len(sys.argv) < 4:
    sys.exit(0)

lb_path, window_s, lift_s = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    window = int(window_s)
    lift_threshold = float(lift_s)
except ValueError:
    sys.exit(0)

try:
    lb = json.load(open(lb_path))
except (OSError, json.JSONDecodeError):
    sys.exit(0)

runs = lb.get("runs") or []
# Only runs with enough metadata to judge staleness
valid = [r for r in runs if isinstance(r, dict)]
if len(valid) < window:
    sys.exit(0)
recent = valid[-window:]


def _metric(run):
    for key in ("primary_metric_mean", "cv_prauc_mean", "cv_mean", "score"):
        value = run.get(key)
        if isinstance(value, (int, float)):
            return value
    return None


def _basis(run):
    return run.get("feature_basis_id") or run.get("feature_basis") or run.get("basis_id")


def _family(run):
    return run.get("model_family") or run.get("family") or run.get("model")


bases = [_basis(r) for r in recent]
families = [_family(r) for r in recent]
metrics = [_metric(r) for r in recent]

if None in bases or None in families:
    sys.exit(0)  # not enough metadata to judge
if len(set(bases)) > 1 or len(set(families)) > 1:
    sys.exit(0)  # diversity already present

clean = [m for m in metrics if m is not None]
if len(clean) < 2:
    sys.exit(0)
lift = max(clean) - min(clean)

if lift < lift_threshold:
    print("=== STALE-BASIS NUDGE ===")
    print(
        f"Last {window} runs: basis={bases[0]}, family={families[0]}, "
        f"lift={lift:.4f} (threshold {lift_threshold})."
    )
    print(
        "The feature basis and model family have not moved materially. "
        "Consider:"
    )
    print("  - /ds-coach — ask Research Lead for direction")
    print("  - feature-basis rotation (redo perm-importance on current champion)")
    print("  - pattern-area pivot per coverage.json")
    print("before another same-family run is started.")
PYEOF

exit 0
