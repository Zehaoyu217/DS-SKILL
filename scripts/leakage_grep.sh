#!/usr/bin/env bash
# Exits 1 if any leakage pattern hits, 0 otherwise.
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
# clean_pipeline.py contains "Pipeline" which legitimizes fit_transform inside; allow override:
if grep -q 'Pipeline\s*(' "$path" && [ $hits -eq 1 ] && ! grep -nE '\.fit\(|ds-workspace/holdout' "$path" >/dev/null ; then
  hits=0
fi
exit $hits
