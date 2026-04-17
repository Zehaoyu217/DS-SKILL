#!/usr/bin/env python3
"""Log a run to an external experiment tracker (MLflow or W&B) AND the local dashboard.

This is the single entry point for recording a run. It:
1. Writes/updates leaderboard.json (always — the dashboard is the source of truth).
2. If a tracker is configured in state.json, mirrors the run to MLflow or W&B.
3. Optionally logs artifacts (plots, metrics.json, ablation.md, diagnostics).

Usage:
    # Log a run from metrics.json
    python tracker_log.py <ds-workspace> <run-dir>

    # Log with explicit artifact upload
    python tracker_log.py <ds-workspace> <run-dir> --artifacts plots/shap_summary.png plots/pdp_*.png

    # Dry-run (show what would be logged, don't write)
    python tracker_log.py <ds-workspace> <run-dir> --dry-run

The script reads:
    - <ds-workspace>/state.json  → tracker config, mode, current version
    - <run-dir>/metrics.json     → cv_mean, cv_std, etc.
    - <run-dir>/seed.txt         → seed
    - <run-dir>/env.lock         → env hash
    - <run-dir>/data.sha256      → data hash

Exit 0 on success, 1 on missing input, 2 on tracker error (dashboard still updated).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Dashboard (leaderboard.json) — always runs
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically via temp-then-rename (dashboard writer contract)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.rename(path)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _read_budget_spent(run_dir: Path) -> dict | None:
    """Pull compute_hours / api_cost_usd from budget-ledger.json if present.

    The ledger is written by scripts/budget_check.py --account at run completion;
    reading it here surfaces the same numbers on the leaderboard without a separate
    code path. Returns None if the ledger is absent (pre-Iron Law #21 runs).
    """
    ledger = run_dir / "budget-ledger.json"
    if not ledger.exists():
        return None
    try:
        entry = json.loads(ledger.read_text())
        spend = entry.get("spend") or {}
        return {k: spend.get(k) for k in ("compute_hours", "api_cost_usd") if k in spend} or None
    except (ValueError, OSError):
        return None


def _read_override_ids(run_dir: Path, metrics: dict) -> list[str]:
    """Collect override ids that authorised this run.

    Three sources, in priority order:
    1. `metrics.json.override_ids` (explicit — caller knows best).
    2. `run_dir/override_refs.txt` (one id per line — used by Engineer scripts).
    3. Default to empty list.
    """
    if isinstance(metrics.get("override_ids"), list):
        return [str(x) for x in metrics["override_ids"]]
    refs = run_dir / "override_refs.txt"
    if refs.exists():
        return [line.strip() for line in refs.read_text().splitlines() if line.strip()]
    return []


def build_run_record(run_dir: Path, metrics: dict, state: dict) -> dict:
    """Build a leaderboard run record from metrics.json + run artifacts.

    Populates Iron Law #21 (budget_spent), #23 (secondary_metrics), #24 (override_ids),
    and #25 (pattern_area, approach_id) fields from metrics.json when present;
    falls back to adjacent artifact files (budget-ledger.json, override_refs.txt)
    when the metrics file does not carry them directly.
    """
    seed_file = run_dir / "seed.txt"
    data_hash_file = run_dir / "data.sha256"
    env_lock_file = run_dir / "env.lock"

    seed = int(seed_file.read_text().strip()) if seed_file.exists() else 0
    data_sha = data_hash_file.read_text().strip() if data_hash_file.exists() else "unknown"
    env_hash = ""
    if env_lock_file.exists():
        env_hash = hashlib.sha256(env_lock_file.read_bytes()).hexdigest()[:16]

    # Iron Law #23 — secondary metrics. Pass through whatever metrics.json declares;
    # null for any declared-but-unmeasured metric (caller's responsibility). The
    # ship gate verifies all pre-registered secondaries are non-null before shipping.
    secondary_metrics = metrics.get("secondary_metrics")
    if not isinstance(secondary_metrics, dict):
        secondary_metrics = {}

    budget_spent = metrics.get("budget_spent")
    if not isinstance(budget_spent, dict):
        budget_spent = _read_budget_spent(run_dir)

    record = {
        "id": run_dir.name,
        "v": state.get("current_v", state.get("current_version", 1)),
        "created_at": now_iso(),
        "model": metrics.get("model", "unknown"),
        "params_summary": metrics.get("params_summary", ""),
        "features_used": metrics.get("features_used", 0),
        "feature_groups": metrics.get("feature_groups", []),
        "cv_mean": metrics["cv_mean"],
        "cv_std": metrics["cv_std"],
        "cv_ci95": metrics.get("cv_ci95", [
            metrics["cv_mean"] - 1.96 * metrics["cv_std"],
            metrics["cv_mean"] + 1.96 * metrics["cv_std"],
        ]),
        "lift_vs_baseline": metrics.get("lift_vs_baseline", 0.0),
        "feature_lift_vs_feature_baseline": metrics.get("feature_lift_vs_feature_baseline", None),
        "tuning_lift_vs_default": metrics.get("tuning_lift_vs_default", None),
        "status": metrics.get("status", "valid"),
        "invalidation_reason": metrics.get("invalidation_reason", None),
        "notes_ref": metrics.get("notes_ref", ""),
        "baseline": metrics.get("baseline", False),
        "feature_baseline": metrics.get("feature_baseline", False),
        "default_params": metrics.get("default_params", False),
        "tuning_run": metrics.get("tuning_run", False),
        "mini_loop": metrics.get("mini_loop", False),
        "provisional": metrics.get("provisional", False),
        "seed": seed,
        "seed_std": metrics.get("seed_std", None),
        "n_seeds": metrics.get("n_seeds", len(metrics.get("seeds", [1]))),
        "data_sha256": data_sha,
        "env_lock_hash": env_hash,
        "commit_sha": metrics.get("commit_sha", None),
        "secondary_metrics": secondary_metrics,
        "pattern_area": metrics.get("pattern_area"),
        "approach_id": metrics.get("approach_id"),
        "override_ids": _read_override_ids(run_dir, metrics),
    }
    if budget_spent is not None:
        record["budget_spent"] = budget_spent
    return record


def update_leaderboard(ws: Path, run_record: dict) -> Path:
    """Add or update a run in leaderboard.json. Returns the path written."""
    lb_path = ws / "dashboard" / "data" / "leaderboard.json"
    lb = load_json(lb_path) if lb_path.exists() else {
        "project": ws.parent.name,
        "primary_metric": {"name": "TBD", "direction": "max"},
        "current_state": {"v": 1, "phase": "FEATURE_MODEL", "updated_at": now_iso()},
        "runs": [], "disproven": [], "events": [],
    }

    # Upsert: replace if run id already exists, else append
    existing_ids = {r["id"] for r in lb["runs"]}
    if run_record["id"] in existing_ids:
        lb["runs"] = [run_record if r["id"] == run_record["id"] else r for r in lb["runs"]]
    else:
        lb["runs"].append(run_record)

    lb["current_state"]["updated_at"] = now_iso()
    atomic_write_json(lb_path, lb)
    return lb_path


def append_event(ws: Path, run_id: str, event_type: str = "run_logged") -> None:
    """Append a line to events.ndjson."""
    events_path = ws / "dashboard" / "data" / "events.ndjson"
    entry = json.dumps({
        "timestamp": now_iso(),
        "run_id": run_id,
        "event": event_type,
    })
    with open(events_path, "a") as f:
        f.write(entry + "\n")


def _load_autonomous_yaml(ws: Path) -> dict:
    """Read autonomous.yaml from the project root (ws.parent). Empty dict if absent or unparseable.

    The file lives outside ds-workspace/ so it survives /ds reset; see templates/autonomous.yaml
    header for the rationale. Parser falls back to a minimal hand-rolled key=value scan when
    PyYAML is unavailable — the only fields this helper consumes are shallow scalars.
    """
    yaml_path = ws.parent / "autonomous.yaml"
    if not yaml_path.exists():
        return {}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(yaml_path.read_text()) or {}
    except ImportError:
        config: dict = {}
        stack: list[tuple[int, dict]] = [(0, config)]
        for raw in yaml_path.read_text().splitlines():
            line = raw.rstrip()
            if not line or line.lstrip().startswith("#") or ":" not in line:
                continue
            indent = len(line) - len(line.lstrip())
            key, _, value = line.strip().partition(":")
            value = value.strip().split("#", 1)[0].strip()
            while stack and indent < stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if not value:
                child: dict = {}
                parent[key] = child
                stack.append((indent + 2, child))
            else:
                try:
                    parent[key] = int(value)
                except ValueError:
                    parent[key] = value
        return config


def maybe_snapshot_leaderboard(ws: Path, current_v: int) -> Path | None:
    """Copy leaderboard.json → dashboard/snapshots/vN-leaderboard.json every N versions.

    N comes from `autonomous.yaml.logging.dashboard_snapshot_every_n_versions`. When the file
    or field is absent, no snapshot is taken (interactive runs opt out by default). Snapshots
    let post-hoc reviewers see the dashboard state *as of* a specific version — useful for the
    Meta-Auditor's trajectory review (Iron Law #25) and for surrender-card ceiling evidence.
    Returns the snapshot path when one was written, else None.
    """
    config = _load_autonomous_yaml(ws)
    cadence = (config.get("logging") or {}).get("dashboard_snapshot_every_n_versions")
    try:
        cadence_int = int(cadence) if cadence is not None else 0
    except (TypeError, ValueError):
        return None
    if cadence_int <= 0 or current_v <= 0 or current_v % cadence_int != 0:
        return None
    lb_path = ws / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        return None
    snap_dir = ws / "dashboard" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snap_dir / f"v{current_v}-leaderboard.json"
    atomic_write_json(snap_path, json.loads(lb_path.read_text()))
    return snap_path


# ---------------------------------------------------------------------------
# MLflow integration
# ---------------------------------------------------------------------------

def log_to_mlflow(run_record: dict, metrics: dict, artifact_paths: list[Path],
                  tracker_config: dict, dry_run: bool) -> bool:
    """Log run to MLflow. Returns True on success."""
    try:
        import mlflow
    except ImportError:
        print("warn: mlflow not installed. Run: pip install mlflow", file=sys.stderr)
        return False

    experiment = tracker_config.get("experiment", tracker_config.get("project", "ds-iteration"))
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "file:./mlruns")

    if dry_run:
        print(f"[dry-run] MLflow: tracking_uri={tracking_uri}, experiment={experiment}")
        print(f"[dry-run] MLflow: params={_mlflow_params(run_record, metrics)}")
        print(f"[dry-run] MLflow: metrics={_mlflow_metrics(run_record, metrics)}")
        print(f"[dry-run] MLflow: artifacts={[str(p) for p in artifact_paths]}")
        return True

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)

    with mlflow.start_run(run_name=f"v{run_record['v']}_{run_record['id']}") as run:
        # Tags
        mlflow.set_tags({
            "version": str(run_record["v"]),
            "status": run_record["status"],
            "baseline": str(run_record["baseline"]),
            "model": run_record["model"],
            "data_sha256": run_record["data_sha256"],
        })

        # Params
        mlflow.log_params(_mlflow_params(run_record, metrics))

        # Metrics
        mlflow.log_metrics(_mlflow_metrics(run_record, metrics))

        # Artifacts
        for path in artifact_paths:
            if path.exists():
                if path.is_dir():
                    mlflow.log_artifacts(str(path), artifact_path=path.name)
                else:
                    mlflow.log_artifact(str(path))

        print(f"MLflow: logged run {run.info.run_id} to experiment '{experiment}'")
    return True


def _mlflow_params(run_record: dict, metrics: dict) -> dict:
    params = {
        "model": run_record["model"],
        "features_used": str(run_record["features_used"]),
        "seed": str(run_record["seed"]),
        "n_seeds": str(run_record.get("n_seeds", 1)),
    }
    if run_record.get("params_summary"):
        params["params_summary"] = run_record["params_summary"][:250]  # MLflow 250 char limit
    if run_record.get("feature_groups"):
        params["feature_groups"] = ", ".join(run_record["feature_groups"])[:250]
    # Add any custom params from metrics.json
    for k in ("cv_scheme", "n_folds", "tuning_method"):
        if k in metrics:
            params[k] = str(metrics[k])
    return params


def _mlflow_metrics(run_record: dict, metrics: dict) -> dict:
    m = {
        "cv_mean": run_record["cv_mean"],
        "cv_std": run_record["cv_std"],
        "cv_ci95_low": run_record["cv_ci95"][0],
        "cv_ci95_high": run_record["cv_ci95"][1],
        "lift_vs_baseline": run_record["lift_vs_baseline"],
    }
    if run_record.get("seed_std") is not None:
        m["seed_std"] = run_record["seed_std"]
    # Pass through any extra numeric metrics from metrics.json
    for k, v in metrics.items():
        if k not in m and isinstance(v, (int, float)) and k not in ("features_used", "seed"):
            m[k] = v
    return m


# ---------------------------------------------------------------------------
# Weights & Biases integration
# ---------------------------------------------------------------------------

def log_to_wandb(run_record: dict, metrics: dict, artifact_paths: list[Path],
                 tracker_config: dict, dry_run: bool) -> bool:
    """Log run to Weights & Biases. Returns True on success."""
    try:
        import wandb
    except ImportError:
        print("warn: wandb not installed. Run: pip install wandb", file=sys.stderr)
        return False

    project = tracker_config.get("project", "ds-iteration")

    if dry_run:
        print(f"[dry-run] W&B: project={project}")
        print(f"[dry-run] W&B: config={_wandb_config(run_record, metrics)}")
        print(f"[dry-run] W&B: metrics={_mlflow_metrics(run_record, metrics)}")
        print(f"[dry-run] W&B: artifacts={[str(p) for p in artifact_paths]}")
        return True

    run = wandb.init(
        project=project,
        name=f"v{run_record['v']}_{run_record['id']}",
        config=_wandb_config(run_record, metrics),
        tags=[f"v{run_record['v']}", run_record["status"], run_record["model"]],
        reinit=True,
    )

    # Log metrics
    wandb.log(_mlflow_metrics(run_record, metrics))

    # Log artifacts as images or files
    for path in artifact_paths:
        if path.exists():
            if path.suffix in (".png", ".jpg", ".jpeg", ".svg"):
                wandb.log({path.stem: wandb.Image(str(path))})
            elif path.is_file():
                artifact = wandb.Artifact(
                    name=f"run_{run_record['id']}_{path.stem}",
                    type="run_artifact",
                )
                artifact.add_file(str(path))
                run.log_artifact(artifact)

    # Summary
    wandb.summary["status"] = run_record["status"]
    wandb.summary["baseline"] = run_record["baseline"]
    wandb.summary["data_sha256"] = run_record["data_sha256"]

    print(f"W&B: logged run {run.id} to project '{project}'")
    wandb.finish()
    return True


def _wandb_config(run_record: dict, metrics: dict) -> dict:
    config = {
        "model": run_record["model"],
        "features_used": run_record["features_used"],
        "seed": run_record["seed"],
        "n_seeds": run_record.get("n_seeds", 1),
        "version": run_record["v"],
        "baseline": run_record["baseline"],
    }
    if run_record.get("feature_groups"):
        config["feature_groups"] = run_record["feature_groups"]
    if run_record.get("params_summary"):
        config["params_summary"] = run_record["params_summary"]
    for k in ("cv_scheme", "n_folds", "tuning_method"):
        if k in metrics:
            config[k] = metrics[k]
    return config


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_artifacts(run_dir: Path, patterns: list[str] | None) -> list[Path]:
    """Resolve artifact file patterns relative to run_dir."""
    if not patterns:
        # Default: metrics.json + all plots + ablation
        defaults = [
            run_dir / "metrics.json",
            run_dir / "ablation.md",
        ]
        plots_dir = run_dir / "plots"
        if plots_dir.exists():
            defaults.append(plots_dir)
        return [p for p in defaults if p.exists()]

    result = []
    for pat in patterns:
        # Support globs relative to run_dir
        matches = glob.glob(str(run_dir / pat))
        if matches:
            result.extend(Path(m) for m in matches)
        else:
            # Try absolute
            matches = glob.glob(pat)
            result.extend(Path(m) for m in matches)
    return [p for p in result if p.exists()]


def patch_commit_sha(ws: Path, run_id: str, sha: str) -> None:
    """Patch the commit_sha field on an existing leaderboard run record."""
    lb_path = ws / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        print(f"error: {lb_path} not found", file=sys.stderr)
        return
    lb = load_json(lb_path)
    patched = False
    for run in lb["runs"]:
        if run["id"] == run_id:
            run["commit_sha"] = sha
            patched = True
            break
    if patched:
        atomic_write_json(lb_path, lb)
        print(f"Dashboard: patched commit_sha={sha[:12]}… on run '{run_id}'")
    else:
        print(f"warn: run id '{run_id}' not found in leaderboard — sha not patched", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Log a run to dashboard + external tracker")
    ap.add_argument("workspace", type=Path, help="path to ds-workspace/")
    ap.add_argument("run_dir", type=Path, help="path to runs/vN/ directory")
    ap.add_argument("--artifacts", nargs="*", help="extra artifact paths/globs to upload")
    ap.add_argument("--dry-run", action="store_true", help="show what would be logged")
    ap.add_argument("--update-sha", metavar="SHA",
                    help="patch commit_sha field on an existing run (used by log_run_commit.sh)")
    ap.add_argument("--run-id", metavar="RUN_ID",
                    help="run id to patch when using --update-sha")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    run_dir = args.run_dir.resolve()

    # --- --update-sha shortcut: patch sha on existing run, then exit ---
    if args.update_sha:
        run_id = args.run_id or run_dir.name
        patch_commit_sha(ws, run_id, args.update_sha)
        return 0

    # --- Validate inputs ---
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        print(f"error: {metrics_path} not found", file=sys.stderr)
        return 1

    state_path = ws / "state.json"
    if not state_path.exists():
        print(f"error: {state_path} not found — run init_workspace.py first", file=sys.stderr)
        return 1

    metrics = load_json(metrics_path)
    state = load_json(state_path)

    # --- Build run record ---
    run_record = build_run_record(run_dir, metrics, state)

    if args.dry_run:
        print("=== Dashboard run record ===")
        print(json.dumps(run_record, indent=2))

    # --- Step 1: Always update dashboard ---
    if not args.dry_run:
        lb_path = update_leaderboard(ws, run_record)
        append_event(ws, run_record["id"], "run_logged")
        print(f"Dashboard: updated {lb_path}")
        snap_path = maybe_snapshot_leaderboard(ws, run_record["v"])
        if snap_path is not None:
            print(f"Dashboard: snapshot written to {snap_path}")

    # --- Step 2: External tracker (if configured) ---
    tracker = state.get("tracker")
    tracker_config = state.get("tracker_config", {})
    artifact_paths = resolve_artifacts(run_dir, args.artifacts)

    tracker_ok = True
    if tracker == "mlflow":
        tracker_ok = log_to_mlflow(run_record, metrics, artifact_paths, tracker_config, args.dry_run)
    elif tracker == "wandb":
        tracker_ok = log_to_wandb(run_record, metrics, artifact_paths, tracker_config, args.dry_run)
    elif tracker is not None and tracker != "null":
        print(f"warn: unknown tracker '{tracker}' in state.json — skipping external log", file=sys.stderr)

    if not tracker_ok:
        print("warn: external tracker failed — dashboard was still updated", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
