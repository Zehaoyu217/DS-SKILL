#!/usr/bin/env python3
"""Lock and verify the eval harness in src/evaluation/ (Iron Law #20).

Computes a combined sha256 over all .py files in src/evaluation/ and writes
or checks the hash in data-contract.md under the "## Eval harness lock" section.

Usage:
    # Write lock at AUDIT exit (first time or after approved override):
    python hash_eval_harness.py <ds-workspace>

    # Verify lock at FEATURE_MODEL / VALIDATE / SHIP entry:
    python hash_eval_harness.py <ds-workspace> --check

Exit codes:
    0  — lock written successfully, OR hash matches (check mode)
    1  — hash mismatch detected (check mode) → fires eval-harness-tampered event
    2  — workspace malformed or src/evaluation/ is empty
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def compute_harness_hash(eval_dir: Path) -> tuple[str, list[str]]:
    """Return (combined_sha256, sorted list of .py files hashed)."""
    py_files = sorted(
        p for p in eval_dir.rglob("*.py")
        if "__pycache__" not in str(p)
    )
    if not py_files:
        return "", []

    combined = hashlib.sha256()
    for f in py_files:
        combined.update(f.read_bytes())
    return combined.hexdigest(), [str(f.relative_to(eval_dir.parent.parent)) for f in py_files]


LOCK_SECTION_RE = re.compile(
    r"(## Eval harness lock\n.*?)(?=\n##|\Z)", re.DOTALL
)

LOCK_SECTION_TEMPLATE = """\
## Eval harness lock
<!-- Written by scripts/hash_eval_harness.py at AUDIT exit. Do not edit manually. -->
eval_harness_sha256: {sha}
locked_at: {ts}
locked_files:
{files}
"""


def read_locked_hash(data_contract: Path) -> str | None:
    """Return the stored sha256 from data-contract.md, or None if not locked."""
    text = data_contract.read_text()
    m = re.search(r"eval_harness_sha256:\s*(\S+)", text)
    if not m or m.group(1) in ("(not yet locked)", ""):
        return None
    return m.group(1)


def write_lock(data_contract: Path, sha: str, files: list[str]) -> None:
    """Insert or replace the ## Eval harness lock section in data-contract.md."""
    file_list = "\n".join(f"  - {f}" for f in files)
    new_section = LOCK_SECTION_TEMPLATE.format(sha=sha, ts=now_iso(), files=file_list)

    text = data_contract.read_text()
    if LOCK_SECTION_RE.search(text):
        text = LOCK_SECTION_RE.sub(new_section.rstrip(), text)
    else:
        text = text.rstrip() + "\n\n" + new_section
    data_contract.write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser(description="Lock or verify the eval harness (Iron Law #20)")
    ap.add_argument("workspace", type=Path, help="path to ds-workspace/")
    ap.add_argument("--check", action="store_true",
                    help="verify mode: compare current hash to stored hash")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    eval_dir = ws / "src" / "evaluation"
    data_contract = ws / "data-contract.md"

    if not eval_dir.exists():
        print(f"error: {eval_dir} does not exist — init_workspace.py may not have run", file=sys.stderr)
        return 2

    if not data_contract.exists():
        print(f"error: {data_contract} does not exist — init_workspace.py may not have run", file=sys.stderr)
        return 2

    sha, files = compute_harness_hash(eval_dir)

    if not sha:
        print(
            f"error: {eval_dir} contains no .py files. "
            "Write your primary metric function in src/evaluation/ before locking.",
            file=sys.stderr,
        )
        return 2

    if args.check:
        stored = read_locked_hash(data_contract)
        if stored is None:
            print(
                "error: eval harness not yet locked in data-contract.md. "
                "Run without --check at AUDIT exit first.",
                file=sys.stderr,
            )
            return 1
        if sha != stored:
            print(
                "EVAL-HARNESS-TAMPERED: src/evaluation/ has changed since it was locked.\n"
                f"  stored hash:  {stored}\n"
                f"  current hash: {sha}\n"
                "Per Iron Law #20, all runs logged since the last valid hash must be reviewed.\n"
                "To legitimately update the evaluator: run `override eval-harness <reason>`, "
                "then re-run without --check to write the new lock.\n"
                "Affected runs must be individually marked valid or invalidated.",
                file=sys.stderr,
            )
            return 1
        print(f"eval harness OK: {sha[:12]}… ({len(files)} file(s) verified)")
        return 0

    # Write mode
    write_lock(data_contract, sha, files)
    print(f"eval harness locked: {sha[:12]}… ({len(files)} file(s))")
    for f in files:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
