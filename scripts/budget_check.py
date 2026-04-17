#!/usr/bin/env python3
"""Budget envelope check + ledger append (Iron Law #21).

Called by the orchestrator before and after every modeling run. Sums the
append-only ledger in `<ds-workspace>/budget.json` against the FRAME-declared
envelopes and reports remaining headroom per dimension. When `--account` is
given, appends a ledger entry and writes `runs/vN/<run_id>/budget-ledger.json`.
If any dimension hits <= 0, emits `budget-exceeded` to
`<ds-workspace>/state.json.events_history` (idempotent) and exits 3.

Usage:
    # Read-only check (defaults to current_v from state.json):
    python3 budget_check.py <ds-workspace> --check
    python3 budget_check.py <ds-workspace> --check --vN 3

    # Per-run accounting (mutates budget.json + state.json + run ledger):
    python3 budget_check.py <ds-workspace> \\
        --account run-v3-002 --vN 3 --cost compute_hours=0.5,api_cost_usd=0.12

Exit codes:
    0  OK — all remaining dimensions > 0.
    2  Argument / IO / schema error.
    3  Budget exceeded — at least one remaining dimension <= 0. Orchestrator
       must obtain an Iron Law #24 override (law=budget) or fall through to
       Iron Law #22 auto-defeat (autonomous mode).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Cost dimensions accepted in --cost. Kept in lockstep with budget.schema.json
# ledger.items.spend properties — if you add a dimension there, add it here too.
COST_KEYS = ("compute_hours", "api_cost_usd")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def parse_cost(raw: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"cost segment must be KEY=VALUE (got {part!r})")
        key, val = part.split("=", 1)
        key = key.strip()
        if key not in COST_KEYS:
            raise ValueError(
                f"unknown cost dimension {key!r}; allowed: {', '.join(COST_KEYS)}"
            )
        try:
            num = float(val.strip())
        except ValueError as exc:
            raise ValueError(f"cost value for {key} must be a number (got {val!r})") from exc
        if num < 0:
            raise ValueError(f"cost value for {key} must be >= 0 (got {num})")
        out[key] = num
    return out


def compute_remaining(budget: dict, state_current_v: int, for_vN: int | None = None) -> dict:
    """Return remaining headroom per envelope dimension. None = unlimited cap."""
    envs = budget.get("envelopes", {}) or {}
    ledger = budget.get("ledger", []) or []

    spent_hours = sum(float((e.get("spend") or {}).get("compute_hours") or 0) for e in ledger)
    spent_usd = sum(float((e.get("spend") or {}).get("api_cost_usd") or 0) for e in ledger)

    declared_at = budget.get("declared_at") or ""
    try:
        declared_dt = datetime.fromisoformat(declared_at.replace("Z", "+00:00"))
        elapsed_days = (datetime.now(timezone.utc) - declared_dt).total_seconds() / 86400.0
    except (ValueError, TypeError):
        elapsed_days = 0.0

    # max_versions counts distinct versions observed so far; state.current_v is authoritative,
    # but ledger entries may belong to a higher vN if run logging outpaced state update.
    max_vN_seen = max((int(e.get("vN") or 0) for e in ledger), default=0)
    active_v = max(int(state_current_v or 1), max_vN_seen)

    def remain(cap, used):
        return None if cap is None else cap - used

    remaining = {
        "compute_hours": remain(envs.get("compute_hours"), spent_hours),
        "api_cost_usd": remain(envs.get("api_cost_usd"), spent_usd),
        "wall_clock_days": remain(envs.get("wall_clock_days"), elapsed_days),
        "max_versions": remain(envs.get("max_versions"), active_v),
    }
    if for_vN is not None:
        cap_runs = envs.get("max_runs_per_version")
        if cap_runs is None:
            remaining["max_runs_per_version"] = None
        else:
            used = sum(1 for e in ledger if int(e.get("vN") or 0) == for_vN)
            remaining["max_runs_per_version"] = cap_runs - used
    return remaining


def dimensions_exhausted(remaining: dict) -> list[str]:
    return [k for k, v in remaining.items() if v is not None and v <= 0]


def format_status(remaining: dict, envs: dict, for_vN: int | None) -> str:
    lines = []
    for key in ("compute_hours", "api_cost_usd", "wall_clock_days", "max_versions"):
        cap = envs.get(key)
        rem = remaining.get(key)
        if cap is None:
            lines.append(f"  {key}: (unlimited)")
        else:
            # :.4g collapses integer caps to '10' rather than '10.00' while keeping enough
            # precision for fractional hours; the cap is printed verbatim for clarity.
            lines.append(f"  {key}: remaining {rem:.4g} / {cap}")
    if for_vN is not None:
        cap = envs.get("max_runs_per_version")
        rem = remaining.get("max_runs_per_version")
        if cap is None:
            lines.append(f"  max_runs_per_version (v{for_vN}): (unlimited)")
        else:
            lines.append(f"  max_runs_per_version (v{for_vN}): remaining {rem} / {cap}")
    return "\n".join(lines)


def append_budget_exceeded_event(state: dict, vN: int, dimensions: list[str]) -> bool:
    """Idempotently append a budget-exceeded event to state.events_history.

    Returns True iff a new entry was appended. De-dup key is (event, ref, v) so
    a re-run at the same version reporting the same dimensions is a no-op.
    """
    ref = f"budget.json#{','.join(sorted(dimensions))}"
    history = state.setdefault("events_history", [])
    for existing in history:
        if (
            existing.get("event") == "budget-exceeded"
            and existing.get("ref") == ref
            and int(existing.get("v", -1)) == vN
        ):
            return False
    history.append({
        "v": vN,
        "event": "budget-exceeded",
        "ref": ref,
        "at": now_iso(),
    })
    return True


def _load_state(state_path: Path, fallback_v: int) -> tuple[dict, bool]:
    if state_path.exists():
        return load_json(state_path), True
    return {"current_v": fallback_v, "events_history": []}, False


def cmd_check(ws: Path, vN_arg: int | None) -> int:
    budget = load_json(ws / "budget.json")
    state_path = ws / "state.json"
    state, state_on_disk = _load_state(state_path, fallback_v=1)
    current_v = int(state.get("current_v") or 1)
    check_vN = vN_arg if vN_arg is not None else current_v

    remaining = compute_remaining(budget, current_v, for_vN=check_vN)
    print(f"# budget status (v{check_vN}, declared {budget.get('declared_at')})")
    print(format_status(remaining, budget.get("envelopes", {}), check_vN))

    exhausted = dimensions_exhausted(remaining)
    if exhausted:
        _report_exceeded(budget, state, state_path, state_on_disk, check_vN, exhausted, remaining)
        return 3

    print("\nOK: all remaining dimensions > 0.")
    print(json.dumps({"status": "OK", "remaining": remaining}, indent=2))
    return 0


def cmd_account(ws: Path, run_id: str, vN: int, cost: dict) -> int:
    budget_path = ws / "budget.json"
    budget = load_json(budget_path)
    state_path = ws / "state.json"
    state, state_on_disk = _load_state(state_path, fallback_v=vN)

    entry = {
        "run_id": run_id,
        "vN": vN,
        "at": now_iso(),
        "spend": {k: cost.get(k, 0.0) for k in COST_KEYS if k in cost},
    }
    budget.setdefault("ledger", []).append(entry)
    save_json(budget_path, budget)

    run_ledger_path = ws / f"runs/v{vN}/{run_id}" / "budget-ledger.json"
    save_json(run_ledger_path, entry)

    remaining = compute_remaining(budget, int(state.get("current_v") or vN), for_vN=vN)
    print(f"# budget charged for run {run_id} (v{vN})")
    print(f"  spend: {json.dumps(entry['spend'])}")
    print(f"  ledger entry written to {run_ledger_path.relative_to(ws)}")
    print(format_status(remaining, budget.get("envelopes", {}), vN))

    exhausted = dimensions_exhausted(remaining)
    if exhausted:
        _report_exceeded(budget, state, state_path, state_on_disk, vN, exhausted, remaining, entry)
        return 3

    print("\nOK: all remaining dimensions > 0.")
    print(json.dumps({"status": "OK", "remaining": remaining, "ledger_entry": entry}, indent=2))
    return 0


def _report_exceeded(budget: dict, state: dict, state_path: Path, state_on_disk: bool,
                     vN: int, exhausted: list[str], remaining: dict,
                     entry: dict | None = None) -> None:
    print(f"\nBUDGET EXCEEDED on: {', '.join(exhausted)}")
    overrides = budget.get("overrides_applied") or []
    if overrides:
        print(f"  active budget override ids on record: {', '.join(overrides)}")
        print("  orchestrator must verify each override is still valid at the next gate.")
    else:
        print("  no active budget overrides — orchestrator MUST refuse further runs until")
        print("  an Iron Law #24 override (law=budget) is filed OR Iron Law #22 auto-defeat fires.")

    if state_on_disk:
        if append_budget_exceeded_event(state, vN, exhausted):
            save_json(state_path, state)
            print("  -> budget-exceeded event appended to state.events_history")
        else:
            print("  -> budget-exceeded event already present in state.events_history (no-op)")

    payload = {"status": "EXCEEDED", "dimensions": exhausted, "remaining": remaining}
    if entry is not None:
        payload["ledger_entry"] = entry
    print(json.dumps(payload, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Iron Law #21 budget envelope check + ledger append.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("workspace", type=Path, help="path to ds-workspace/")
    ap.add_argument("--account", help="run_id to record ledger entry under (mutates budget.json)")
    ap.add_argument("--vN", type=int,
                    help="version number for the ledger entry / check scope (default: state.current_v)")
    ap.add_argument("--cost", help="comma-separated KEY=VALUE spend (compute_hours, api_cost_usd)")
    ap.add_argument("--check", action="store_true",
                    help="read-only mode: report remaining envelope and exit")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    if not (ws / "budget.json").exists():
        print(
            f"ERROR: no budget.json at {ws}/budget.json — declare at FRAME exit (Iron Law #21)",
            file=sys.stderr,
        )
        return 2

    try:
        if args.account:
            if args.vN is None:
                print("ERROR: --vN is required with --account", file=sys.stderr)
                return 2
            if not args.cost:
                print("ERROR: --cost is required with --account", file=sys.stderr)
                return 2
            cost = parse_cost(args.cost)
            if not cost:
                print("ERROR: --cost parsed to an empty dict; specify at least one dimension",
                      file=sys.stderr)
                return 2
            return cmd_account(ws, args.account, args.vN, cost)
        # --check (default when no --account provided)
        return cmd_check(ws, args.vN)
    except FileNotFoundError as exc:
        print(f"ERROR: file not found: {exc}", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
