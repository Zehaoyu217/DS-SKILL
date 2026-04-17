#!/usr/bin/env bash
# log_run_commit.sh — Structured git commit for a ds-workspace run (Item 4).
#
# Creates an immutable audit-trail commit so `git log --grep="ds-run:"` serves
# as a searchable experiment history. Only call this for PROMOTED runs (full K-fold
# ceremony complete). Do NOT call during mini-loop provisional iterations.
#
# Usage:
#   bash log_run_commit.sh <workspace> <run-dir> <run-id> <description> [--dry-run]
#
# Arguments:
#   workspace    Path to ds-workspace/
#   run-dir      Path to the run directory (e.g. runs/v1)
#   run-id       Short run identifier (e.g. "v1_lgbm_baseline")
#   description  One-line note (e.g. "LightGBM baseline, raw features")
#   --dry-run    Print the commit message without committing
#
# Commit message format (git log --grep-able):
#   ds-run: v{N}/{run-id} [{PHASE}] {metric}={cv_mean:.4f}±{cv_std:.4f}
#
#   model: {model}
#   phase: {phase}
#   baseline: {true|false}
#   feature_baseline: {true|false}
#   lift_vs_baseline: {value:+.4f}
#   seeds: {seeds}
#   data_sha256: {sha[:12]}
#   status: {status}
#   note: {description}
#
# After commit, writes the commit sha back to leaderboard.json via tracker_log.py --update-sha.
#
# IMPORTANT: Never amend or rebase commits created by this script — they are
# immutable audit artifacts. Each run gets its own commit.

set -euo pipefail

WORKSPACE="${1:?Usage: log_run_commit.sh <workspace> <run-dir> <run-id> <description> [--dry-run]}"
RUN_DIR="${2:?}"
RUN_ID="${3:?}"
DESCRIPTION="${4:?}"
DRY_RUN="${5:-}"

WORKSPACE="$(cd "$WORKSPACE" && pwd)"
RUN_DIR="$(cd "$RUN_DIR" && pwd)"
METRICS="$RUN_DIR/metrics.json"

# ── Validate ──────────────────────────────────────────────────────────────────
if [ ! -f "$METRICS" ]; then
  echo "error: $METRICS not found" >&2
  exit 1
fi

# Check git repo — non-blocking if absent
if ! git -C "$WORKSPACE" rev-parse --git-dir > /dev/null 2>&1; then
  echo "warn: $WORKSPACE is not inside a git repository — skipping commit (non-blocking)" >&2
  exit 0
fi

# ── Parse metrics.json ────────────────────────────────────────────────────────
CV_MEAN=$(python3 -c "import json,sys; d=json.load(open('$METRICS')); print(f\"{d['cv_mean']:.4f}\")")
CV_STD=$(python3  -c "import json,sys; d=json.load(open('$METRICS')); print(f\"{d.get('cv_std',0):.4f}\")")
MODEL=$(python3   -c "import json,sys; d=json.load(open('$METRICS')); print(d.get('model','unknown'))")
PHASE=$(python3   -c "import json,sys; d=json.load(open('$METRICS')); print(d.get('phase','FEATURE_MODEL'))")
BASELINE=$(python3 -c "import json,sys; d=json.load(open('$METRICS')); print(str(d.get('baseline',False)).lower())")
FEAT_BL=$(python3  -c "import json,sys; d=json.load(open('$METRICS')); print(str(d.get('feature_baseline',False)).lower())")
LIFT=$(python3     -c "import json,sys; d=json.load(open('$METRICS')); v=d.get('lift_vs_baseline',0); print(f'{v:+.4f}')")
SEEDS=$(python3    -c "import json,sys; d=json.load(open('$METRICS')); print(','.join(str(s) for s in d.get('seeds',[d.get('seed',0)])))")
STATUS=$(python3   -c "import json,sys; d=json.load(open('$METRICS')); print(d.get('status','valid'))")

DATA_SHA="unknown"
if [ -f "$RUN_DIR/data.sha256" ]; then
  DATA_SHA="$(head -c 12 "$RUN_DIR/data.sha256")"
fi

# Version from run-dir name (e.g. "v1" or "v2")
VERSION="$(basename "$RUN_DIR")"

# ── Build commit message ──────────────────────────────────────────────────────
SUBJECT="ds-run: $VERSION/$RUN_ID [$PHASE] ${MODEL}=${CV_MEAN}±${CV_STD}"

BODY="model: $MODEL
phase: $PHASE
baseline: $BASELINE
feature_baseline: $FEAT_BL
lift_vs_baseline: $LIFT
seeds: $SEEDS
data_sha256: $DATA_SHA
status: $STATUS
note: $DESCRIPTION"

FULL_MSG="$SUBJECT

$BODY"

# ── Dry-run mode ──────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = "--dry-run" ]; then
  echo "=== Dry-run: commit message ==="
  echo "$FULL_MSG"
  exit 0
fi

# ── Stage run artifacts ───────────────────────────────────────────────────────
# Stage only specific run artifacts — never git add -A (avoids .env etc.)
GIT_ROOT="$(git -C "$WORKSPACE" rev-parse --show-toplevel)"

# Resolve paths relative to git root for git add
REL_METRICS="$(realpath --relative-to="$GIT_ROOT" "$METRICS")"
git -C "$GIT_ROOT" add "$REL_METRICS"

for extra in ablation.md seed.txt env.lock data.sha256; do
  f="$RUN_DIR/$extra"
  if [ -f "$f" ]; then
    rel="$(realpath --relative-to="$GIT_ROOT" "$f")"
    git -C "$GIT_ROOT" add "$rel"
  fi
done

# Stage plots directory if it exists
PLOTS="$RUN_DIR/plots"
if [ -d "$PLOTS" ]; then
  rel="$(realpath --relative-to="$GIT_ROOT" "$PLOTS")"
  git -C "$GIT_ROOT" add "$rel"
fi

# Stage leaderboard.json (updated by tracker_log.py just before this call)
LB="$WORKSPACE/dashboard/data/leaderboard.json"
if [ -f "$LB" ]; then
  rel="$(realpath --relative-to="$GIT_ROOT" "$LB")"
  git -C "$GIT_ROOT" add "$rel"
fi

# ── Commit ────────────────────────────────────────────────────────────────────
git -C "$GIT_ROOT" commit -m "$FULL_MSG"

# ── Write sha back to leaderboard.json ───────────────────────────────────────
COMMIT_SHA="$(git -C "$GIT_ROOT" rev-parse HEAD)"

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$SKILL_DIR/scripts/tracker_log.py" "$WORKSPACE" "$RUN_DIR" \
  --update-sha "$COMMIT_SHA" --run-id "$RUN_ID"

echo "Run committed: $COMMIT_SHA"
echo "  subject: $SUBJECT"
