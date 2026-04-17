#!/usr/bin/env python3
"""Validate a submission file against sample_submission.csv.

Checks: row count, ID set equality and order, column names and order, dtypes,
no NaN/Inf in prediction columns, and probability range [0,1] when the sample
template looks like probabilities (values in [0,1]).

Usage:
    python check_submission_format.py submission.csv sample_submission.csv

Exits 0 on PASS, non-zero on any failure. Prints a structured report.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _load(path: Path):
    import pandas as pd
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: check_submission_format.py <submission> <sample_submission>", file=sys.stderr)
        return 2

    try:
        import numpy as np
        import pandas as pd
    except ImportError as e:
        print(f"missing dependency: {e}", file=sys.stderr)
        return 3

    sub_path = Path(argv[1])
    sample_path = Path(argv[2])
    if not sub_path.exists() or not sample_path.exists():
        print(f"file not found: {sub_path} or {sample_path}", file=sys.stderr)
        return 4

    sub = _load(sub_path)
    sample = _load(sample_path)

    errors: list[str] = []
    warnings: list[str] = []

    if list(sub.columns) != list(sample.columns):
        errors.append(f"column mismatch: submission={list(sub.columns)} sample={list(sample.columns)}")

    if len(sub) != len(sample):
        errors.append(f"row count mismatch: submission={len(sub)} sample={len(sample)}")

    id_col = sample.columns[0]
    if id_col in sub.columns and id_col in sample.columns:
        sub_ids = set(sub[id_col].astype(str).tolist())
        sample_ids = set(sample[id_col].astype(str).tolist())
        if sub_ids != sample_ids:
            missing = sample_ids - sub_ids
            extra = sub_ids - sample_ids
            errors.append(f"id set mismatch: missing={len(missing)} extra={len(extra)}")
        elif len(sub) == len(sample) and not (sub[id_col].astype(str).values == sample[id_col].astype(str).values).all():
            warnings.append("id order differs from sample (many organizers accept this; verify)")

    for col in sample.columns:
        if col not in sub.columns:
            continue
        if sample[col].dtype != sub[col].dtype:
            warnings.append(f"dtype mismatch for {col}: submission={sub[col].dtype} sample={sample[col].dtype}")

    for col in sub.columns:
        if col == id_col:
            continue
        series = sub[col]
        if series.isna().any():
            errors.append(f"NaN in prediction column {col}")
        if np.issubdtype(series.dtype, np.number):
            if np.isinf(series.values).any():
                errors.append(f"Inf in prediction column {col}")
            if col in sample.columns and np.issubdtype(sample[col].dtype, np.number):
                s_min, s_max = float(sample[col].min()), float(sample[col].max())
                if 0.0 <= s_min and s_max <= 1.0:
                    if series.min() < -1e-6 or series.max() > 1.0 + 1e-6:
                        errors.append(f"{col}: looks like probability in sample but submission range is [{series.min()}, {series.max()}]")

    import hashlib
    sub_bytes = sub_path.read_bytes()
    sha = hashlib.sha256(sub_bytes).hexdigest()

    print("# submission format check")
    print(f"submission: {sub_path}")
    print(f"sample:     {sample_path}")
    print(f"sha256:     {sha}")
    print(f"rows:       {len(sub)} (sample: {len(sample)})")
    print(f"columns:    {list(sub.columns)}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")
        print("\nVERDICT: FAIL")
        return 1
    print("\nVERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
