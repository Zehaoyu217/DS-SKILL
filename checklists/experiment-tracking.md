# Checklist: Experiment Tracking Integration

Optional integration with external experiment trackers. The built-in dashboard (`leaderboard.json` + live HTML) remains the source of truth for all gate decisions. The external tracker is a mirror for team collaboration and long-term persistence.

## How it works

`scripts/tracker_log.py` is the single entry point for recording a run. It:

1. **Always** updates `dashboard/data/leaderboard.json` (atomic write-temp-then-rename)
2. **Always** appends to `dashboard/data/events.ndjson`
3. **If configured**, mirrors the run to MLflow or W&B with metrics, params, tags, and artifacts

```bash
# Basic usage — logs to dashboard + configured tracker
python $SKILL/scripts/tracker_log.py ds-workspace runs/v1

# With explicit artifact upload
python $SKILL/scripts/tracker_log.py ds-workspace runs/v1 --artifacts "plots/*.png" ablation.md

# Dry-run (preview what would be logged)
python $SKILL/scripts/tracker_log.py ds-workspace runs/v1 --dry-run
```

The orchestrator calls `tracker_log.py` at FEATURE_MODEL step 6 (after model diagnostics) and at SHIP (final artifacts). Manual invocation is also supported.

## Configuration

Set in `state.json`:

```json
{
  "tracker": "mlflow",
  "tracker_config": {
    "project": "my-project",
    "experiment": "v1-gbm-exploration"
  }
}
```

Valid values for `tracker`: `"mlflow"`, `"wandb"`, `null` (dashboard-only, default).

## MLflow integration

### Setup
```bash
pip install mlflow
export MLFLOW_TRACKING_URI=<uri>   # local: "file:./mlruns" or remote server URL
```

### What gets logged per run
- **Tags**: version (vN), status (valid/invalidated/superseded), baseline flag, model type, data_sha256
- **Parameters**: model, features_used, seed, n_seeds, feature_groups, cv_scheme, n_folds, tuning_method, params_summary
- **Metrics**: cv_mean, cv_std, cv_ci95_low, cv_ci95_high, lift_vs_baseline, seed_std, plus any extra numeric fields in metrics.json
- **Artifacts**: metrics.json, ablation.md, plots/ directory (SHAP, PDP, ICE, calibration, segment plots)

### When to log
- At FEATURE_MODEL: after each CV run completes, diagnostics run, and metrics.json is written
- At VALIDATE: after expanded predicted interval is computed (update existing run)
- At SHIP: final model artifacts and report

## Weights & Biases integration

### Setup
```bash
pip install wandb
export WANDB_API_KEY=<key>
export WANDB_PROJECT=<project>
```

### What gets logged per run
Same data as MLflow, using W&B equivalents:
- `wandb.config` for parameters
- `wandb.log()` for metrics
- `wandb.log({"shap_summary": wandb.Image(...)})` for diagnostic plots (auto-detected from .png/.jpg/.svg)
- `wandb.summary` for status and data hash
- `wandb.Artifact` for non-image files (metrics.json, ablation.md)

## Dashboard ↔ Tracker consistency

The dashboard is always updated first, and tracker failure does NOT block the pipeline. If `tracker_log.py` exits 2 (tracker error), the run is still on the dashboard and the gate can proceed. This ensures external infrastructure issues never block modeling work.

The tracker mirrors the dashboard, not the other way around. If you need to reconcile, the dashboard (`leaderboard.json`) is the source of truth.

## Verification
- [ ] Tracker configured in `state.json` (or explicitly set to `null`)
- [ ] Environment variables set (if tracker is non-null)
- [ ] `python $SKILL/scripts/tracker_log.py ds-workspace runs/v1 --dry-run` succeeds
- [ ] Test run logged successfully before FEATURE_MODEL begins
- [ ] Dashboard `leaderboard.json` still updated regardless of tracker status
- [ ] If tracker fails, pipeline continues (exit 2, not exit 1)
