#!/usr/bin/env python3
"""Bootstrap a ds-workspace/ inside a project folder.

Creates the directory tree defined by workspace-layout.md, copies dashboard-template/,
seeds lessons.md / step-journal / sandbox notebook from templates/, writes initial
state.json + leaderboard.json, and (optionally) starts the dashboard server.

Idempotent: existing files are never overwritten; missing ones are filled in.

Usage:
    python init_workspace.py [--project-root PATH] [--no-server] [--force]

Exit 0 on success, 2 on validation failure.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]

SUBDIRS = [
    "holdout",
    "plans",
    "findings",
    "disproven",
    "literature",
    "audits",
    "runs",
    "nb",
    "src/data",
    "src/features",
    "src/models",
    "src/evaluation",
    "step-journal",
    "dashboard/assets",
    "dashboard/data",
    "overrides",
]

SEED_COPIES = [
    # (skill-relative src, workspace-relative dest)
    ("dashboard-template/index.html",       "dashboard/index.html"),
    ("dashboard-template/assets/styles.css","dashboard/assets/styles.css"),
    ("dashboard-template/assets/app.js",    "dashboard/assets/app.js"),
    ("dashboard-template/assets/charts.js", "dashboard/assets/charts.js"),
    ("templates/lessons.md",                "lessons.md"),
    ("templates/step-journal.md",           "step-journal/v1.md"),
    ("templates/sandbox-vN.ipynb",          "nb/v1_sandbox.ipynb"),
    ("templates/learnings-vN.md",           "runs/v1/learnings.md"),
    ("templates/user-guidance.md",          "USER_GUIDANCE.md"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def copy_if_missing(src: Path, dst: Path) -> bool:
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def init(project_root: Path, start_server: bool, force: bool) -> int:
    ws = project_root / "ds-workspace"
    if ws.exists() and not force and (ws / "state.json").exists():
        print(f"ds-workspace already initialized at {ws}. use --force to re-seed missing files.")
        # still fill in missing files
    for sub in SUBDIRS:
        (ws / sub).mkdir(parents=True, exist_ok=True)

    created = []
    for rel_src, rel_dst in SEED_COPIES:
        if copy_if_missing(SKILL_ROOT / rel_src, ws / rel_dst):
            created.append(rel_dst)

    state = {
        "project": project_root.name,
        "initialized_at": now_iso(),
        "current_version": 1,
        "current_phase": "FRAME",
        "holdout_reads": 0,
        "competition_mode": None,
        "submitted": False,
        "skill_version": "v3",
    }
    if write_if_missing(ws / "state.json", json.dumps(state, indent=2) + "\n"):
        created.append("state.json")

    leaderboard = {
        "project": project_root.name,
        "primary_metric": {"name": "TBD", "direction": "max"},
        "current_state": {"v": 1, "phase": "FRAME"},
        "runs": [],
        "disproven": [],
        "events": [],
    }
    if write_if_missing(ws / "dashboard/data/leaderboard.json", json.dumps(leaderboard, indent=2) + "\n"):
        created.append("dashboard/data/leaderboard.json")

    # HOLDOUT_LOCK placeholder — real lock is written when holdout is split
    if write_if_missing(ws / "holdout/HOLDOUT_LOCK.txt",
                        "DO NOT READ. Lock will be finalized when holdout is split at DGP exit.\n"):
        created.append("holdout/HOLDOUT_LOCK.txt")

    # Initial data-contract stub
    if write_if_missing(ws / "data-contract.md",
                        "# Data Contract\n\nFill in during FRAME phase — columns, types, labels, time window, expected rows.\n"):
        created.append("data-contract.md")

    print(f"# ds-workspace initialized at {ws}")
    print(f"files seeded: {len(created)}")
    for c in created:
        print(f"  + {c}")

    if start_server:
        server = SKILL_ROOT / "server" / "serve_dashboard.py"
        if server.exists():
            print(f"\nstarting dashboard server: python3 {server} {ws}/dashboard/")
            try:
                subprocess.Popen(
                    [sys.executable, str(server), str(ws / "dashboard")],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("server started in background; tail dashboard/server.log for output.")
            except OSError as e:
                print(f"warn: could not start server ({e}); start manually: python3 {server} {ws}/dashboard/")
        else:
            print(f"warn: dashboard server script not found at {server}")

    print("\nnext: answer the five framing questions, draft plans/v1.md, sign the DGP memo.")
    print(f"see: {SKILL_ROOT / 'SKILL.md'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, default=Path.cwd(),
                    help="project folder (default: cwd)")
    ap.add_argument("--no-server", action="store_true", help="skip launching the dashboard server")
    ap.add_argument("--force", action="store_true",
                    help="re-seed missing files even if ds-workspace/ already exists")
    args = ap.parse_args()

    root = args.project_root.resolve()
    if not root.exists():
        print(f"project root does not exist: {root}", file=sys.stderr)
        return 2

    return init(root, start_server=not args.no_server, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
