"""Smoke tests for gate scripts: consistency_lint and hash_eval_harness."""
from __future__ import annotations

import json
import pathlib
import sys
import textwrap

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.consistency_lint import run as lint_run
from scripts.hash_eval_harness import (
    compute_harness_hash,
    read_locked_hash,
    write_lock,
)


# ---------------------------------------------------------------------------
# consistency_lint
# ---------------------------------------------------------------------------

def test_lint_missing_workspace(tmp_path):
    """Non-existent workspace produces exactly one 'workspace.missing' error."""
    report = lint_run(tmp_path / "no-such-workspace")
    errors = [i for i in report.issues if i.severity == "error"]
    assert len(errors) == 1
    assert errors[0].code == "workspace.missing"


def test_lint_empty_workspace_passes(tmp_path):
    """An empty but existing workspace produces no errors (no artifacts to check)."""
    ws = tmp_path / "ds-workspace"
    ws.mkdir()
    report = lint_run(ws)
    errors = [i for i in report.issues if i.severity == "error"]
    assert errors == []


def test_lint_hypothesis_marked_resolved_without_card_is_error(tmp_path):
    """A hypothesis with status != 'open' but no card → plan.hypothesis-missing-card error."""
    ws = tmp_path / "ds-workspace"
    (ws / "plans").mkdir(parents=True)
    plan_md = textwrap.dedent("""\
        ---
        name: plan-v1
        version: 1
        hypotheses:
          - id: h001
            text: feature X helps
            status: confirmed
        ---
        # Plan v1
    """)
    (ws / "plans" / "v1.md").write_text(plan_md)
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "plan.hypothesis-missing-card" in codes


def test_lint_resolved_hypothesis_no_error(tmp_path):
    """A hypothesis resolved by a finding card → no unresolved error."""
    ws = tmp_path / "ds-workspace"
    (ws / "plans").mkdir(parents=True)
    (ws / "findings").mkdir(parents=True)

    plan_md = textwrap.dedent("""\
        ---
        name: plan-v1
        version: 1
        hypotheses:
          - id: h001
            text: feature X helps
        ---
        # Plan v1
    """)
    finding_md = textwrap.dedent("""\
        ---
        id: f001
        hypothesis_id: h001
        verdict: confirmed
        ---
        # Finding f001
    """)
    (ws / "plans" / "v1.md").write_text(plan_md)
    (ws / "findings" / "v1-f001.md").write_text(finding_md)

    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.hypothesis-unresolved" not in codes


# ---------------------------------------------------------------------------
# hash_eval_harness — unit-level
# ---------------------------------------------------------------------------

def test_compute_harness_hash_empty_dir(tmp_path):
    """Empty evaluation dir returns empty hash and empty file list."""
    sha, files = compute_harness_hash(tmp_path)
    assert sha == ""
    assert files == []


def test_compute_harness_hash_stable(tmp_path):
    """Same file content always produces the same sha256."""
    (tmp_path / "metric.py").write_text("def evaluate(y, p): return (y == p).mean()\n")
    sha1, files1 = compute_harness_hash(tmp_path)
    sha2, files2 = compute_harness_hash(tmp_path)
    assert sha1 == sha2
    assert sha1 != ""
    assert len(files1) == 1


def test_compute_harness_hash_changes_on_edit(tmp_path):
    """Modifying a file changes the hash."""
    f = tmp_path / "metric.py"
    f.write_text("def evaluate(y, p): return 0\n")
    sha_before, _ = compute_harness_hash(tmp_path)
    f.write_text("def evaluate(y, p): return 1\n")
    sha_after, _ = compute_harness_hash(tmp_path)
    assert sha_before != sha_after


def test_read_locked_hash_absent(tmp_path):
    """data-contract.md with no lock section returns None."""
    dc = tmp_path / "data-contract.md"
    dc.write_text("# Data Contract\n\nNo lock here.\n")
    assert read_locked_hash(dc) is None


def test_write_lock_and_read_back(tmp_path):
    """write_lock inserts a section; read_locked_hash retrieves the same sha."""
    dc = tmp_path / "data-contract.md"
    dc.write_text("# Data Contract\n")
    sha = "abc123def456"
    write_lock(dc, sha, ["src/evaluation/metric.py"])
    assert read_locked_hash(dc) == sha


def test_write_lock_idempotent(tmp_path):
    """Calling write_lock twice replaces the section rather than appending."""
    dc = tmp_path / "data-contract.md"
    dc.write_text("# Data Contract\n")
    write_lock(dc, "first_sha", ["src/evaluation/metric.py"])
    write_lock(dc, "second_sha", ["src/evaluation/metric.py"])
    content = dc.read_text()
    assert content.count("eval_harness_sha256") == 1
    assert read_locked_hash(dc) == "second_sha"


def test_write_check_roundtrip(tmp_path):
    """Full write-then-check cycle: hash matches → read_locked_hash equals computed sha."""
    eval_dir = tmp_path / "src" / "evaluation"
    eval_dir.mkdir(parents=True)
    (eval_dir / "metric.py").write_text("def evaluate(y, p): return (y == p).mean()\n")
    dc = tmp_path / "data-contract.md"
    dc.write_text("# Data Contract\n")

    sha, files = compute_harness_hash(eval_dir)
    write_lock(dc, sha, files)

    stored = read_locked_hash(dc)
    assert stored == sha

    # Simulate --check: recompute and compare
    sha2, _ = compute_harness_hash(eval_dir)
    assert sha2 == stored


# ---------------------------------------------------------------------------
# consistency_lint — Iron Laws #21-25 checks
# ---------------------------------------------------------------------------

def _write_plan_v1(ws: pathlib.Path, *, secondary: list[dict] | None) -> None:
    (ws / "plans").mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "name: plan-v1",
        "version: 1",
        "pre_registration:",
        "  primary_metric: auroc",
    ]
    if secondary is not None:
        lines.append("  secondary_metrics:")
        for m in secondary:
            lines.append(f"    - name: {m['name']}")
            lines.append(f"      direction: {m.get('direction', 'min')}")
            lines.append(f"      max_degradation_sigma: {m.get('sigma', 2.0)}")
    lines += [
        "hypotheses: []",
        "---",
        "# Plan v1",
        "",
    ]
    (ws / "plans" / "v1.md").write_text("\n".join(lines))


def test_lint_anti_goodhart_missing(tmp_path):
    """Iron Law #23 — plan v1 with <2 secondary_metrics errors out."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}])
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.anti-goodhart-missing" in codes


def test_lint_anti_goodhart_passes_with_two_secondaries(tmp_path):
    """Iron Law #23 — plan v1 with >=2 secondaries passes."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece", "direction": "min"},
            {"name": "worst_segment_score", "direction": "max"},
        ],
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.anti-goodhart-missing" not in codes


def test_lint_budget_missing_errors(tmp_path):
    """Iron Law #21 — plan v1 exists but budget.json does not → error."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece"},
            {"name": "worst_segment_score"},
        ],
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.budget-missing" in codes


def test_lint_coverage_missing_errors(tmp_path):
    """Iron Law #25 — plan v1 exists but coverage.json does not → error."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece"},
            {"name": "worst_segment_score"},
        ],
    )
    (ws / "budget.json").write_text(
        json.dumps({"declared_at": "2026-04-16T00:00:00Z", "envelopes": {"compute_hours": 10}, "ledger": []})
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.coverage-missing" in codes


def test_lint_coverage_stale_warning(tmp_path):
    """Iron Law #25 — coverage.json exists but last_tried_vN is far behind current_v."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece"},
            {"name": "worst_segment_score"},
        ],
    )
    (ws / "budget.json").write_text(
        json.dumps({"declared_at": "2026-04-16T00:00:00Z", "envelopes": {"compute_hours": 10}, "ledger": []})
    )
    (ws / "coverage.json").write_text(
        json.dumps({
            "project": "t",
            "updated_at": "2026-01-01T00:00:00Z",
            "pattern_areas": [{
                "name": "data-quality",
                "approaches_tried": [{"approach": "baseline", "vN": 1, "outcome": "neutral"}],
                "last_tried_vN": 1,
                "exhausted": False,
                "remaining_leverage_estimate": 0.5,
            }],
        })
    )
    (ws / "state.json").write_text(
        json.dumps({
            "current_v": 5, "phase": "FEATURE_MODEL", "mode": "daily", "seed": 1,
            "data_sha256": "a" * 64, "env_lock_hash": "h",
            "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
            "active_hypotheses": [], "open_blockers": [], "events_history": [],
        })
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "warning"}
    assert "lint.coverage-stale" in codes


def test_lint_override_missing_artifact_errors(tmp_path):
    """Iron Law #24 — state.active_overrides lists an id with no backing override file."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece"},
            {"name": "worst_segment_score"},
        ],
    )
    (ws / "budget.json").write_text(
        json.dumps({"declared_at": "2026-04-16T00:00:00Z", "envelopes": {"compute_hours": 10}, "ledger": []})
    )
    (ws / "coverage.json").write_text(
        json.dumps({
            "project": "t",
            "updated_at": "2026-04-16T00:00:00Z",
            "pattern_areas": [{
                "name": "data-quality",
                "approaches_tried": [{"approach": "baseline", "vN": 1, "outcome": "neutral"}],
                "last_tried_vN": 1,
                "exhausted": False,
                "remaining_leverage_estimate": 0.5,
            }],
        })
    )
    (ws / "state.json").write_text(
        json.dumps({
            "current_v": 1, "phase": "FRAME", "mode": "daily", "seed": 1,
            "data_sha256": "a" * 64, "env_lock_hash": "h",
            "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
            "active_hypotheses": [], "open_blockers": [], "events_history": [],
            "active_overrides": ["override-v1-001"],
        })
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-missing-artifact" in codes


def test_lint_surrender_required_when_aborted(tmp_path):
    """Iron Law #22 — state.phase=ABORTED but no surrender-vN.md → error."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(
        ws,
        secondary=[
            {"name": "calibration_ece"},
            {"name": "worst_segment_score"},
        ],
    )
    (ws / "budget.json").write_text(
        json.dumps({"declared_at": "2026-04-16T00:00:00Z", "envelopes": {"compute_hours": 10}, "ledger": []})
    )
    (ws / "coverage.json").write_text(
        json.dumps({
            "project": "t", "updated_at": "2026-04-16T00:00:00Z",
            "pattern_areas": [{
                "name": "data-quality",
                "approaches_tried": [{"approach": "baseline", "vN": 1, "outcome": "neutral"}],
                "last_tried_vN": 1, "exhausted": True,
                "remaining_leverage_estimate": 0.1,
            }],
        })
    )
    (ws / "state.json").write_text(
        json.dumps({
            "current_v": 3, "phase": "ABORTED", "mode": "daily", "seed": 1,
            "data_sha256": "a" * 64, "env_lock_hash": "h",
            "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
            "active_hypotheses": [], "open_blockers": [], "events_history": [],
        })
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.surrender-missing" in codes


# ---------------------------------------------------------------------------
# Regression: override signed_by scalar + reverse-sync drift + meta-audit monotonic
# ---------------------------------------------------------------------------

def _write_override_card(ws: pathlib.Path, oid: str, *, law: str, scope: str,
                         signed_by, expires_at: str | None = None, vN: int = 1) -> pathlib.Path:
    """Write an override-card with chosen signed_by (scalar or list) and scope.

    signed_by is injected verbatim — scalars reproduce the regression path.
    """
    (ws / "overrides").mkdir(parents=True, exist_ok=True)
    path = ws / "overrides" / f"v{vN}-override-{oid}.md"
    lines = [
        "---",
        f"id: {oid}",
        f"law: {law}",
        f"scope: {scope}",
        f"vN: {vN}",
    ]
    if expires_at is not None:
        lines.append(f"expires_at: {expires_at}")
    if isinstance(signed_by, list):
        lines.append("signed_by:")
        for s in signed_by:
            lines.append(f"  - {s}")
    else:
        lines.append(f"signed_by: {signed_by}")
    lines += ["---", "", f"# override {oid}", ""]
    path.write_text("\n".join(lines))
    return path


def test_lint_override_signed_by_scalar_errors(tmp_path):
    """Regression: signed_by as scalar string silently passes per-char iteration.

    The bug — pre-fix, a scalar "user,council" string would iterate character-by-character,
    each single char failing the core-law 'user' membership check but producing no error.
    check_overrides must now surface lint.override-signed-by-not-list for any non-list value.
    """
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 1, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": ["override-v1-scalar"],
    }))
    _write_override_card(
        ws, "override-v1-scalar",
        law="1", scope="permanent",
        signed_by="user,council",  # BUG shape: scalar string, not a list
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-signed-by-not-list" in codes, f"got {codes}"
    # Scalar signed_by MUST NOT silently satisfy the core-law human-signer check —
    # the permanent-quorum check should also fire because the scalar coerces to [].
    assert "lint.override-permanent-quorum-missing" in codes


def test_lint_override_reverse_sync_orphan_warns(tmp_path):
    """Regression: disk has a permanent-scope override card, state.active_overrides omits it.

    Reverse-sync drift is a warning (not error) but must surface so the linter catches
    operators editing state.json directly and forgetting the filesystem side.
    """
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 2, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": [],
    }))
    _write_override_card(
        ws, "override-v1-orphan",
        law="anti-goodhart", scope="permanent",
        signed_by=["user", "council"],
        vN=1,
    )
    report = lint_run(ws)
    warn_codes = {i.code for i in report.issues if i.severity == "warning"}
    assert "lint.override-orphan-file" in warn_codes, f"got {warn_codes}"


def test_lint_meta_audit_fabricated(tmp_path):
    """Iron Law #22/#24 anti-gaming — last_meta_audit_v with no artifact on disk = error."""
    ws = tmp_path / "ds-workspace"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(json.dumps({
        "current_v": 10, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "last_meta_audit_v": 10,  # claims an audit that never happened on disk
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.meta-audit-fabricated" in codes, f"got {codes}"


def test_lint_meta_audit_matches_disk_passes(tmp_path):
    """Iron Law #22/#24 anti-gaming — last_meta_audit_v with matching artifact = no error."""
    ws = tmp_path / "ds-workspace"
    (ws / "audits" / "meta").mkdir(parents=True)
    (ws / "audits" / "meta" / "v10-meta-audit.md").write_text("---\nverdict: PASS\n---\n")
    (ws / "state.json").write_text(json.dumps({
        "current_v": 10, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "last_meta_audit_v": 10,
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.meta-audit-fabricated" not in codes
    assert "lint.meta-audit-future-dated" not in codes


def test_lint_meta_audit_future_dated(tmp_path):
    """Iron Law anti-gaming — last_meta_audit_v > current_v is nonsensical."""
    ws = tmp_path / "ds-workspace"
    ws.mkdir(parents=True)
    (ws / "audits" / "meta").mkdir(parents=True)
    (ws / "audits" / "meta" / "v20-meta-audit.md").write_text("---\nverdict: PASS\n---\n")
    (ws / "state.json").write_text(json.dumps({
        "current_v": 5, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "last_meta_audit_v": 20,  # > current_v
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.meta-audit-future-dated" in codes, f"got {codes}"


def test_lint_meta_audit_honors_custom_dir(tmp_path):
    """meta_audit_artifact_dir in autonomous.yaml controls where the linter looks for artifacts."""
    ws = tmp_path / "ds-workspace"
    (ws / "reviews" / "meta").mkdir(parents=True)
    (ws / "reviews" / "meta" / "v10-meta-audit.md").write_text("---\nverdict: PASS\n---\n")
    (tmp_path / "autonomous.yaml").write_text(
        "logging:\n  meta_audit_artifact_dir: reviews/meta/\n"
    )
    (ws / "state.json").write_text(json.dumps({
        "current_v": 10, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "last_meta_audit_v": 10,
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    # With the custom dir honored, the artifact is found and no fabrication error fires.
    assert "lint.meta-audit-fabricated" not in codes, f"custom dir not honored; got {codes}"


# ---------------------------------------------------------------------------
# Regression: slug-form law id canonicalization, orphan core-permanent, permanent #20/#16 rejection
# ---------------------------------------------------------------------------

def test_lint_override_slug_eval_harness_permanent_rejected(tmp_path):
    """Iron Law #20 — scope=permanent for eval-harness (slug form) is forbidden outright.

    Audit C found that `law: eval-harness` silently bypassed the core-law human-signer
    check because the guard used string-exact equality against `{"1","12","17","20"}`.
    LAW_SLUG_TO_ID now canonicalizes both numeric and slug forms; LAWS_REJECT_PERMANENT
    refuses scope=permanent for #16 + #20 regardless of signers.
    """
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 1, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": ["override-v1-harness"],
    }))
    _write_override_card(
        ws, "override-v1-harness",
        law="eval-harness", scope="permanent",  # slug form
        signed_by=["user", "council-a", "council-b"],  # quorum PLUS human present
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-permanent-forbidden" in codes, f"slug-form #20 permanent not rejected; got {codes}"


def test_lint_override_slug_dgp_permanent_requires_human(tmp_path):
    """Iron Law #24 — `law: dgp` (slug form) is canonicalized to #12 and still requires human signer."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 1, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": ["override-v1-dgp"],
    }))
    _write_override_card(
        ws, "override-v1-dgp",
        law="dgp", scope="permanent",
        signed_by=["council-a", "council-b", "council-c"],  # no 'user'
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-core-law-no-human" in codes, f"slug-form #12 permanent bypassed human check; got {codes}"


def test_lint_override_slug_consistency_permanent_requires_human(tmp_path):
    """`law: consistency` (slug form for #17) must still require a 'user' signer at permanent scope."""
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 1, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": ["override-v1-consistency"],
    }))
    _write_override_card(
        ws, "override-v1-consistency",
        law="consistency", scope="permanent",
        signed_by=["council-a", "council-b"],
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-core-law-no-human" in codes, f"slug-form #17 permanent bypassed human check; got {codes}"


def test_lint_override_orphan_core_permanent_is_error(tmp_path):
    """An orphaned scope=permanent override of a core law (#1,#12,#17,#20,#16,budget) is an error.

    Non-core-law orphan is a warning; core-law permanent orphan upgrades to error so
    operators can't silently drop a holdout-integrity override by editing state.json.
    """
    ws = tmp_path / "ds-workspace"
    _write_plan_v1(ws, secondary=[{"name": "calibration_ece"}, {"name": "worst_segment_score"}])
    (ws / "state.json").write_text(json.dumps({
        "current_v": 2, "phase": "FRAME", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z", "holdout_reads": 0,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
        "active_overrides": [],  # orphaned
    }))
    _write_override_card(
        ws, "override-v1-holdout",
        law="holdout", scope="permanent",  # slug for #1
        signed_by=["user", "council"],
        vN=1,
    )
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.override-orphan-core-permanent" in codes, f"core-permanent orphan not escalated to error; got {codes}"


# ---------------------------------------------------------------------------
# Regression: holdout_reads integrity (Iron Law #1 anti-rollback)
# ---------------------------------------------------------------------------

def test_lint_holdout_reads_rollback(tmp_path):
    """Iron Law #1 — state.holdout_reads was edited down from 1 → 0, but the stamp still exists on disk."""
    ws = tmp_path / "ds-workspace"
    (ws / "audits").mkdir(parents=True)
    (ws / "audits" / "v3-repro.md").write_text(
        "---\nverdict: PASS\n---\n\n# Repro v3\n\nHoldout read once; metric within predicted interval.\n"
    )
    (ws / "state.json").write_text(json.dumps({
        "current_v": 3, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z",
        "holdout_reads": 0,  # rolled back from 1
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.holdout-reads-rollback" in codes, f"holdout rollback not detected; got {codes}"


def test_lint_holdout_reads_fabricated(tmp_path):
    """Iron Law #1 — state.holdout_reads claims more reads than audit stamps on disk support."""
    ws = tmp_path / "ds-workspace"
    ws.mkdir(parents=True)
    (ws / "state.json").write_text(json.dumps({
        "current_v": 3, "phase": "VALIDATE", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z",
        "holdout_reads": 2,  # no audits/v*-repro.md stamps on disk
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.holdout-reads-fabricated" in codes, f"holdout fabrication not detected; got {codes}"


def test_lint_holdout_reads_matches_stamps_passes(tmp_path):
    """Counter == stamps with 'holdout' in the repro doc → no integrity error."""
    ws = tmp_path / "ds-workspace"
    (ws / "audits").mkdir(parents=True)
    (ws / "audits" / "v5-repro.md").write_text(
        "---\nverdict: PASS\n---\n\n# Repro v5\n\nHoldout read once at SHIP_INT.\n"
    )
    (ws / "state.json").write_text(json.dumps({
        "current_v": 5, "phase": "SHIP", "mode": "daily", "seed": 1,
        "data_sha256": "a" * 64, "env_lock_hash": "h",
        "holdout_locked_at": "2026-04-16T00:00:00Z",
        "holdout_reads": 1,
        "active_hypotheses": [], "open_blockers": [], "events_history": [],
    }))
    report = lint_run(ws)
    codes = {i.code for i in report.issues if i.severity == "error"}
    assert "lint.holdout-reads-rollback" not in codes
    assert "lint.holdout-reads-fabricated" not in codes
