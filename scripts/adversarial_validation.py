#!/usr/bin/env python3
"""Adversarial validation: train a classifier to distinguish train from test rows.

Reports mean CV AUC, top drift features, and exact + near-duplicate counts.
Usage:
    python adversarial_validation.py \
        --train data/train.parquet \
        --test data/test.parquet \
        --target target \
        --id id \
        --out ds-workspace/audits/vN-adversarial.md

Lightweight dependencies: pandas, numpy, sklearn, optional lightgbm. Falls back to
sklearn.ensemble.GradientBoostingClassifier when lightgbm is unavailable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(path: Path):
    import pandas as pd
    if path.suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if path.suffix in {".csv", ".tsv"}:
        sep = "\t" if path.suffix == ".tsv" else ","
        return pd.read_csv(path, sep=sep)
    raise SystemExit(f"unsupported file type: {path}")


def _fit_classifier(X, y):
    try:
        import lightgbm as lgb  # type: ignore
        model = lgb.LGBMClassifier(
            n_estimators=300, learning_rate=0.05, num_leaves=31,
            subsample=0.8, colsample_bytree=0.8, random_state=0, verbose=-1,
        )
    except Exception:
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(random_state=0)
    model.fit(X, y)
    return model


def _feature_importances(model, columns):
    if hasattr(model, "feature_importances_"):
        return sorted(zip(columns, model.feature_importances_), key=lambda x: -x[1])
    return []


def _duplicates(train, test, feature_cols):
    exact_dup = train[feature_cols].merge(test[feature_cols], on=feature_cols, how="inner").shape[0]
    return exact_dup


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--id", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top_k", type=int, default=10)
    args = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import roc_auc_score
    except ImportError as e:
        raise SystemExit(f"missing dependency: {e}. pip install pandas scikit-learn (and optionally lightgbm).")

    train = _load(Path(args.train))
    test = _load(Path(args.test))

    drop_cols = {args.target}
    if args.id:
        drop_cols.add(args.id)
    feature_cols = [c for c in train.columns if c not in drop_cols and c in test.columns]
    if not feature_cols:
        raise SystemExit("no overlapping feature columns between train and test")

    X_train = train[feature_cols]
    X_test = test[feature_cols]

    numeric = X_train.select_dtypes(include="number").columns.tolist()
    X_train = X_train[numeric].fillna(-999)
    X_test = X_test[numeric].fillna(-999)

    X = pd.concat([X_train, X_test], ignore_index=True)
    y = np.concatenate([np.zeros(len(X_train)), np.ones(len(X_test))])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    aucs = []
    for fold_idx, (tr, va) in enumerate(skf.split(X, y)):
        model = _fit_classifier(X.iloc[tr], y[tr])
        preds = model.predict_proba(X.iloc[va])[:, 1]
        aucs.append(float(roc_auc_score(y[va], preds)))

    final_model = _fit_classifier(X, y)
    top_features = _feature_importances(final_model, numeric)[: args.top_k]

    dup_count = _duplicates(train, test, numeric)
    dup_ratio = dup_count / max(len(test), 1)

    adv_auc = float(np.mean(aucs))
    adv_std = float(np.std(aucs))

    if adv_auc < 0.55 and dup_ratio < 0.05:
        verdict = "PASS"
    elif adv_auc > 0.75:
        verdict = "BLOCK"
    elif adv_auc > 0.60 or dup_ratio > 0.20:
        verdict = "COVARIATE-SHIFT"
    else:
        verdict = "PASS-WITH-NOTE"

    summary = {
        "adv_auc_mean": adv_auc,
        "adv_auc_std": adv_std,
        "exact_dup_count": int(dup_count),
        "dup_ratio": float(dup_ratio),
        "top_drift_features": [[c, float(i)] for c, i in top_features],
        "verdict": verdict,
        "feature_cols_used": numeric,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Adversarial Validation",
        "",
        f"adv_auc: {adv_auc:.4f}  (CV std: {adv_std:.4f})",
        f"Exact dup count: {dup_count} / {len(test)}  (dup_ratio: {dup_ratio:.4f})",
        f"Verdict: {verdict}",
        "",
        "## Top drift features",
    ]
    for col, imp in top_features:
        lines.append(f"- {col}: {imp:.2f}")
    lines += ["", "## Raw summary (JSON)", "```json", json.dumps(summary, indent=2), "```", ""]
    out.write_text("\n".join(lines))

    print(json.dumps(summary, indent=2))
    return 0 if verdict != "BLOCK" else 2


if __name__ == "__main__":
    sys.exit(main())
