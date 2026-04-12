#!/usr/bin/env bash
set -u
SK=$(cd "$(dirname "$0")/.." && pwd)
fail=0
if "$SK/scripts/leakage_grep.sh" "$SK/scripts/fixtures/leak_scaler.py" ; then
  echo "FAIL: expected leakage grep to flag leak_scaler.py"; fail=1
fi
if ! "$SK/scripts/leakage_grep.sh" "$SK/scripts/fixtures/clean_pipeline.py" ; then
  echo "FAIL: expected leakage grep to pass clean_pipeline.py"; fail=1
fi
exit $fail
