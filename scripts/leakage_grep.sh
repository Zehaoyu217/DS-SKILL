#!/usr/bin/env bash
# Exits 1 if any leakage pattern hits, 0 otherwise.
# Extended patterns cover: fit-before-split, target-encoding, time leaks, holdout touch,
# train+test concat fit, rolling/expanding without min_periods, submission reads at train time.
set -u
path="${1:?usage: leakage_grep.sh <path>}"
hits=0
check() {
  local pattern="$1" desc="$2"
  if grep -nE "$pattern" "$path" >/dev/null 2>&1; then
    grep -nE "$pattern" "$path"
    echo "LEAK: $desc"
    hits=1
  fi
}
check 'fit_transform\(' 'fit_transform — likely leak unless inside Pipeline+cross_val'
check '\.fit\([^)]*X[A-Za-z_]*[^)]*\)' '.fit(X*) at module/cell scope — verify in-fold'
check 'groupby\(.*\)\.(mean|agg|transform)' 'aggregation on full data — target leak risk'
check '(^|[^A-Za-z_])(next_|future_|label_t\+)' 'future-dated feature name'
check 'ds-workspace/holdout/' 'holdout directory read'
check 'pd\.concat\(\[.*train.*test.*\]\)' 'train+test concatenation — verify no fit on this'
check '\.expanding\(\)\.(mean|sum|std)' 'expanding aggregate without min_periods — time leak risk'
check '\.rolling\([^)]*\)\.(mean|sum|std)' 'rolling aggregate — verify min_periods and time-boundary guard'
check 'pd\.factorize\(.*concat' 'factorize on concatenated data — category leak'
check 'read_.*submission' 'submission file read in training code path'
# clean_pipeline.py contains "Pipeline" which legitimizes fit_transform inside; allow override:
if grep -q 'Pipeline\s*(' "$path" && [ $hits -eq 1 ] && ! grep -nE '\.fit\(|ds-workspace/holdout|pd\.concat\(\[.*train.*test|\.expanding\(|\.rolling\(|pd\.factorize\(.*concat|read_.*submission' "$path" >/dev/null ; then
  hits=0
fi
exit $hits
