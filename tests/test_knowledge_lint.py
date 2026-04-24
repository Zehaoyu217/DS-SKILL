"""Smoke tests for scripts/knowledge_lint.py.

Each test constructs a minimal ds-workspace in a tmp_path, runs the linter
via subprocess, and asserts on the JSON report. The linter is warning-only
so we never assert on exit code beyond "not 2".
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
LINTER = SKILL_ROOT / "scripts" / "knowledge_lint.py"


def _make_workspace(tmp_path: Path, kb: str | None, current_version: int = 10) -> Path:
    ws = tmp_path / "ds-workspace"
    ws.mkdir()
    if kb is not None:
        (ws / "knowledge-base.md").write_text(kb)
    (ws / "state.json").write_text(json.dumps({"current_version": current_version}))
    return ws


def _run(ws: Path) -> dict:
    completed = subprocess.run(
        ["python3", str(LINTER), str(ws), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 2, completed.stderr
    return json.loads(completed.stdout)


def _codes(report: dict) -> set[str]:
    return {issue["code"] for issue in report["issues"]}


def test_missing_kb_warns(tmp_path: Path) -> None:
    ws = _make_workspace(tmp_path, kb=None, current_version=1)
    assert "kb.missing" in _codes(_run(ws))


def test_stale_section_warns(tmp_path: Path) -> None:
    kb = "# KB\n\n## 1. Dataset profile\n\nlast_reviewed: v1\n"
    ws = _make_workspace(tmp_path, kb, current_version=10)
    assert "kb.section-stale" in _codes(_run(ws))


def test_fresh_section_no_stale_warning(tmp_path: Path) -> None:
    kb = "# KB\n\n## 1. Dataset profile\n\nlast_reviewed: v10\n"
    ws = _make_workspace(tmp_path, kb, current_version=10)
    assert "kb.section-stale" not in _codes(_run(ws))


def test_unexplored_in_basis_variable_warns(tmp_path: Path) -> None:
    kb = """# KB

## 2. Variable catalog

last_reviewed: v10

```yaml
variables:
  - name: ambient_temp_c
    in_feature_basis: true
    explored: []
```
"""
    ws = _make_workspace(tmp_path, kb, current_version=10)
    assert "kb.variables-in-basis-unexplored" in _codes(_run(ws))


def test_flat_segment_warns(tmp_path: Path) -> None:
    kb = """# KB

## 6. Segment analysis

last_reviewed: v10

```yaml
segments:
  - name: cold
    trend_last_k_versions: flat
```
"""
    ws = _make_workspace(tmp_path, kb, current_version=10)
    assert "kb.segment-flat" in _codes(_run(ws))


def test_stale_open_question_warns(tmp_path: Path) -> None:
    kb = """# KB

## 8. Open questions

- [ ] Q-001 (opened v1): sample question left open too long
"""
    ws = _make_workspace(tmp_path, kb, current_version=10)
    assert "kb.open-questions-stale" in _codes(_run(ws))


def test_clean_kb_no_warnings(tmp_path: Path) -> None:
    kb = """# KB

## 1. Dataset profile

last_reviewed: v10

## 2. Variable catalog

last_reviewed: v10

```yaml
variables:
  - name: x
    in_feature_basis: true
    explored:
      - kind: perm-importance
        vN: v10
```

## 6. Segment analysis

last_reviewed: v10

```yaml
segments:
  - name: warm
    trend_last_k_versions: improving
```
"""
    ws = _make_workspace(tmp_path, kb, current_version=10)
    report = _run(ws)
    # None of the warning codes should fire on a clean KB.
    bad_codes = {
        "kb.missing",
        "kb.section-stale",
        "kb.variables-in-basis-unexplored",
        "kb.segment-flat",
        "kb.segment-regressing",
        "kb.open-questions-stale",
    }
    assert not (_codes(report) & bad_codes), report


@pytest.mark.parametrize(
    "line,expected_in",
    [
        ("- §2 variables — mark foo explored", True),
        ("- §5 insights — append MI-09", True),
        ("- generic bullet, no section ref", False),
    ],
)
def test_unconsumed_synthesis_patches_detected(
    tmp_path: Path, line: str, expected_in: bool
) -> None:
    kb = """# KB

## 2. Variable catalog

last_reviewed: v3

## 5. Model-derived insights

last_reviewed: v3
"""
    ws = _make_workspace(tmp_path, kb, current_version=10)
    audits = ws / "audits"
    audits.mkdir()
    synthesis = audits / "v10-model-synthesis.md"
    synthesis.write_text(
        "# synth\n\n## 7. Proposed KB patches\n\n" + line + "\n"
    )
    codes = _codes(_run(ws))
    if expected_in:
        assert "kb.unconsumed-synthesis-patch" in codes
    else:
        assert "kb.unconsumed-synthesis-patch" not in codes
