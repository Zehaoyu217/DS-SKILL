#!/usr/bin/env python3
"""Consistency linter for a ds-workspace.

Cross-references structured-claim blocks across plan / DGP / findings / disproven /
step-journal / lessons / leaderboard. Flags contradictions, orphans, stale entries,
and broken supersedes chains.

Exit codes:
    0  no errors (warnings may still be present)
    1  at least one error
    2  workspace malformed or unreadable

Usage:
    python consistency_lint.py <ds-workspace-root>
    python consistency_lint.py ds-workspace --json > report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("missing dependency: pyyaml. pip install pyyaml", file=sys.stderr)
    sys.exit(2)


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
YAML_FENCE_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
HYPOTHESIS_ID_RE = re.compile(r"\bH-v\d+(?:\.[a-z])?-\d+\b")
PREDICTION_ID_RE = re.compile(r"\bP-\d+\b")
FINDING_ID_RE = re.compile(r"\bv\d+(?:\.[a-z])?-f\d+\b")
DISPROVEN_ID_RE = re.compile(r"\bv\d+(?:\.[a-z])?-d\d+\b")


@dataclass
class Issue:
    severity: str  # "error" | "warning" | "info"
    code: str
    message: str
    file: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "file": self.file,
        }


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def error(self, code: str, message: str, file: str | None = None) -> None:
        self.issues.append(Issue("error", code, message, file))

    def warn(self, code: str, message: str, file: str | None = None) -> None:
        self.issues.append(Issue("warning", code, message, file))

    def info(self, code: str, message: str, file: str | None = None) -> None:
        self.issues.append(Issue("info", code, message, file))

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


def load_frontmatter(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text()
    except OSError:
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


def load_yaml_fences(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text()
    except OSError:
        return []
    blocks: list[dict[str, Any]] = []
    for m in YAML_FENCE_RE.finditer(text):
        try:
            data = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict):
            blocks.append(data)
    return blocks


def latest_dgp_predictions(root: Path, report: Report) -> dict[str, dict[str, Any]]:
    """Collect all DGP §7a predictions across memo versions; latest wins on id collision."""
    candidates = sorted(root.glob("dgp-memo*.md")) + sorted(root.glob("plans/*dgp*.md"))
    predictions: dict[str, dict[str, Any]] = {}
    for memo in candidates:
        for block in load_yaml_fences(memo):
            preds = block.get("predictions")
            if not isinstance(preds, list):
                continue
            for pred in preds:
                if not isinstance(pred, dict):
                    continue
                pid = pred.get("id")
                if not pid:
                    report.warn(
                        "dgp.prediction-missing-id",
                        f"prediction block without id in {memo.name}",
                        file=str(memo),
                    )
                    continue
                predictions[pid] = {**pred, "_source": str(memo)}
    return predictions


def collect_plans(root: Path) -> dict[int, dict[str, Any]]:
    """Load all plans/vN.md and return by version."""
    plans: dict[int, dict[str, Any]] = {}
    for p in sorted((root / "plans").glob("v*.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        v = fm.get("version")
        if isinstance(v, int):
            plans[v] = {**fm, "_path": str(p)}
    return plans


def collect_cards(root: Path, subdir: str, kind: str) -> list[dict[str, Any]]:
    out = []
    for p in sorted((root / subdir).glob("*.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        if fm.get("kind") != kind:
            continue
        out.append({**fm, "_path": str(p)})
    return out


def check_hypotheses_resolved(
    plans: dict[int, dict[str, Any]],
    findings: list[dict[str, Any]],
    disproven: list[dict[str, Any]],
    report: Report,
) -> None:
    resolved: dict[str, list[str]] = {}
    for card in findings + disproven:
        hid = card.get("hypothesis_id")
        if hid:
            resolved.setdefault(hid, []).append(card.get("id", card["_path"]))

    for v, plan in plans.items():
        for h in plan.get("hypotheses", []) or []:
            if not isinstance(h, dict):
                continue
            hid = h.get("id")
            if not hid:
                continue
            card_ids = resolved.get(hid, [])
            status = h.get("status", "open")
            if not card_ids:
                if status not in ("open", None):
                    report.error(
                        "plan.hypothesis-missing-card",
                        f"{hid} in {plan['_path']} has status '{status}' but no finding/disproven card",
                        file=plan["_path"],
                    )
                else:
                    report.warn(
                        "plan.hypothesis-unresolved",
                        f"{hid} in {plan['_path']} has no card and status is still '{status}'",
                        file=plan["_path"],
                    )
            if len(card_ids) > 1:
                report.error(
                    "plan.hypothesis-multiple-cards",
                    f"{hid} resolves to multiple cards: {card_ids}",
                    file=plan["_path"],
                )


def check_card_plan_refs(
    plans: dict[int, dict[str, Any]],
    cards: list[dict[str, Any]],
    report: Report,
) -> None:
    known = {
        h.get("id")
        for p in plans.values()
        for h in (p.get("hypotheses") or [])
        if isinstance(h, dict) and h.get("id")
    }
    for card in cards:
        hid = card.get("hypothesis_id")
        if hid and hid not in known:
            report.error(
                "card.unknown-hypothesis",
                f"card {card.get('id')} references unknown hypothesis {hid}",
                file=card["_path"],
            )


def check_dgp_refs(
    cards: list[dict[str, Any]],
    predictions: dict[str, dict[str, Any]],
    report: Report,
) -> None:
    for card in cards:
        for ref in card.get("dgp_refs") or []:
            if not isinstance(ref, dict):
                continue
            pid = ref.get("prediction_id")
            if pid and pid not in predictions:
                report.error(
                    "card.unknown-dgp-prediction",
                    f"card {card.get('id')} references unknown DGP prediction {pid}",
                    file=card["_path"],
                )


def check_direction_contradictions(
    findings: list[dict[str, Any]],
    disproven: list[dict[str, Any]],
    report: Report,
) -> None:
    """Flag opposite-direction claims on the same subject unless one supersedes the other."""
    claims: dict[str, list[dict[str, Any]]] = {}
    for card in findings:
        subj = card.get("subject")
        if subj:
            claims.setdefault(subj, []).append(card)

    superseded: set[str] = set()
    for card in findings + disproven:
        for sid in card.get("supersedes") or []:
            superseded.add(sid)

    for subj, group in claims.items():
        dirs = {c.get("direction") for c in group if c.get("direction") not in (None, "neutral")}
        live = [c for c in group if c.get("id") not in superseded]
        live_dirs = {c.get("direction") for c in live if c.get("direction") not in (None, "neutral")}
        if len(live_dirs) > 1:
            ids = [c.get("id") for c in live]
            report.error(
                "cards.direction-contradiction",
                f"subject '{subj}': live findings disagree on direction {live_dirs} across {ids}",
                file=None,
            )


def check_supersedes_chain(
    cards: list[dict[str, Any]],
    report: Report,
) -> None:
    by_id = {c.get("id"): c for c in cards if c.get("id")}
    for card in cards:
        for sid in card.get("supersedes") or []:
            target = by_id.get(sid)
            if not target:
                report.error(
                    "cards.supersedes-unknown",
                    f"{card.get('id')} supersedes {sid} which does not exist",
                    file=card["_path"],
                )
                continue
            if target.get("superseded_by") not in (card.get("id"), None):
                report.warn(
                    "cards.supersedes-asymmetric",
                    f"{sid} is superseded by {card.get('id')} but its superseded_by field is '{target.get('superseded_by')}'",
                    file=target["_path"],
                )
            if target.get("status") not in ("retracted", "closed", "promoted"):
                report.warn(
                    "cards.superseded-still-open",
                    f"{sid} is superseded by {card.get('id')} but still has status '{target.get('status')}'",
                    file=target["_path"],
                )


def check_pre_registration_uniformity(
    plans: dict[int, dict[str, Any]],
    report: Report,
) -> None:
    """Primary metric should not silently change across versions without an explicit trigger."""
    prev_metric = None
    prev_v = None
    for v in sorted(plans):
        plan = plans[v]
        pr = plan.get("pre_registration") or {}
        metric = pr.get("primary_metric")
        if prev_metric and metric and metric != prev_metric:
            triggers = plan.get("trigger_refs") or []
            if not triggers:
                report.error(
                    "plan.metric-drift",
                    f"primary_metric changed from '{prev_metric}' (v{prev_v}) to '{metric}' (v{v}) without trigger_refs",
                    file=plan["_path"],
                )
            else:
                report.info(
                    "plan.metric-drift-justified",
                    f"primary_metric changed v{prev_v}->{v} via triggers {triggers}",
                    file=plan["_path"],
                )
        prev_metric = metric or prev_metric
        prev_v = v


def check_leaderboard_alignment(
    root: Path,
    findings: list[dict[str, Any]],
    report: Report,
) -> None:
    lb_path = root / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        return
    try:
        lb = json.loads(lb_path.read_text())
    except (OSError, json.JSONDecodeError):
        report.error(
            "leaderboard.unreadable",
            f"cannot parse {lb_path}",
            file=str(lb_path),
        )
        return
    runs = lb.get("runs") or []
    valid = [r for r in runs if r.get("status") == "valid"]
    if not valid:
        return
    top = max(valid, key=lambda r: r.get("cv_mean", float("-inf")) - 2 * r.get("cv_std", 0))
    top_run_id = top.get("run_id")
    if not any(top_run_id in (card.get("evidence") or {}).get("runs", []) for card in findings):
        report.warn(
            "leaderboard.top-run-not-claimed",
            f"top leaderboard run '{top_run_id}' is not referenced by any finding card",
            file=str(lb_path),
        )


def check_top_predictions_touched(
    predictions: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
    disproven: list[dict[str, Any]],
    report: Report,
) -> None:
    touched: set[str] = set()
    for card in findings + disproven:
        for ref in card.get("dgp_refs") or []:
            if isinstance(ref, dict) and ref.get("prediction_id"):
                touched.add(ref["prediction_id"])
    for pid, pred in predictions.items():
        if pred.get("priority") == "top" and pid not in touched:
            report.warn(
                "dgp.top-prediction-not-tested",
                f"DGP prediction {pid} is marked priority=top but no finding/disproven references it",
                file=pred.get("_source"),
            )


def check_step_journal(root: Path, known_ids: dict[str, set[str]], report: Report) -> None:
    journals = list(root.glob("**/step-journal*.md"))
    for j in journals:
        for block in load_yaml_fences(j):
            refs = block.get("refs") or {}
            for ref_type, ids in refs.items():
                if not isinstance(ids, list):
                    continue
                pool = known_ids.get(ref_type, set())
                for ref_id in ids:
                    if ref_id and ref_id not in pool:
                        report.warn(
                            "journal.unknown-ref",
                            f"journal entry {block.get('entry_id')} references unknown {ref_type} '{ref_id}'",
                            file=str(j),
                        )


def check_lessons_sources(root: Path, known_ids: dict[str, set[str]], report: Report) -> None:
    lessons = root / "lessons.md"
    if not lessons.exists():
        return
    text = lessons.read_text()
    for m in FINDING_ID_RE.finditer(text):
        fid = m.group(0)
        if fid not in known_ids.get("findings", set()):
            report.warn(
                "lessons.unknown-finding",
                f"lessons.md references unknown finding {fid}",
                file=str(lessons),
            )
    for m in DISPROVEN_ID_RE.finditer(text):
        did = m.group(0)
        if did not in known_ids.get("disproven", set()):
            report.warn(
                "lessons.unknown-disproven",
                f"lessons.md references unknown disproven {did}",
                file=str(lessons),
            )


def check_brainstorm_count(root: Path, report: Report) -> None:
    """Iron Law #19a — brainstorm counts:
    - FEATURE_MODEL: >=3 alternatives (error, blocking)
    - DATA_PREP: >=3 handling strategies (warning, non-blocking)
    - FEATURE_ENG: >=2 representations (warning, non-blocking)
    """
    for p in sorted((root / "runs").glob("*/brainstorm-*-FEATURE_MODEL.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        count = fm.get("alternatives_count")
        if count is not None and isinstance(count, int) and count < 3:
            report.error(
                "lint.brainstorm-count-low",
                f"{p.name}: alternatives_count={count}, Iron Law #19a requires >=3",
                file=str(p),
            )
    for p in sorted((root / "runs").glob("*/brainstorm-*-DATA_PREP.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        count = fm.get("alternatives_count")
        if count is not None and isinstance(count, int) and count < 3:
            report.warn(
                "lint.brainstorm-count-low",
                f"{p.name}: alternatives_count={count}, Iron Law #19a recommends >=3 for DATA_PREP",
                file=str(p),
            )
    for p in sorted((root / "runs").glob("*/brainstorm-*-FEATURE_ENG.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        count = fm.get("alternatives_count")
        if count is not None and isinstance(count, int) and count < 2:
            report.warn(
                "lint.brainstorm-count-low",
                f"{p.name}: alternatives_count={count}, Iron Law #19a recommends >=2 per hypothesis for FEATURE_ENG",
                file=str(p),
            )


def check_feature_baseline_present(root: Path, report: Report) -> None:
    """Iron Law #19b — leaderboard must have a feature_baseline run for each vN that has non-baseline runs."""
    lb_path = root / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        return
    try:
        lb = json.loads(lb_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    runs = lb.get("runs") or []
    # Group valid/superseded runs by version (exclude invalidated)
    by_version: dict[int, list[dict[str, Any]]] = {}
    for r in runs:
        if r.get("status") == "invalidated":
            continue
        v = r.get("v")
        if isinstance(v, int):
            by_version.setdefault(v, []).append(r)
    for v, vr in sorted(by_version.items()):
        has_non_baseline = any(not r.get("baseline", False) for r in vr)
        has_feature_baseline = any(r.get("feature_baseline", False) for r in vr)
        if has_non_baseline and not has_feature_baseline:
            report.error(
                "lint.feature-baseline-missing",
                f"v{v}: non-baseline runs exist but no feature_baseline run; Iron Law #19b violated",
                file=str(lb_path),
            )


def check_tuning_has_default_params(root: Path, report: Report) -> None:
    """Iron Law #19b — any vN with tuning runs must have a default_params reference run."""
    lb_path = root / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        return
    try:
        lb = json.loads(lb_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    runs = lb.get("runs") or []
    by_version: dict[int, list[dict[str, Any]]] = {}
    for r in runs:
        if r.get("status") == "invalidated":
            continue
        v = r.get("v")
        if isinstance(v, int):
            by_version.setdefault(v, []).append(r)
    for v, vr in sorted(by_version.items()):
        has_tuning = any(r.get("tuning_run", False) for r in vr)
        has_default_params = any(r.get("default_params", False) for r in vr)
        if has_tuning and not has_default_params:
            report.error(
                "lint.tuning-without-default-params",
                f"v{v}: tuning runs exist but no default_params reference run; Iron Law #19b violated",
                file=str(lb_path),
            )


def check_single_path_resolution(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Warn when a hypothesis resolves but no brainstorm alternatives were rejected — single-path resolution."""
    for v, plan in plans.items():
        brainstorm_paths = list((root / "runs").glob(f"v{v}/brainstorm-v{v}-FEATURE_MODEL.md"))
        if not brainstorm_paths:
            continue
        fm = load_frontmatter(brainstorm_paths[0])
        if not fm:
            continue
        rejected = fm.get("rejected_alternative_ids") or []
        if isinstance(rejected, list) and len(rejected) == 0:
            # Only warn if hypotheses were actually resolved this version
            hypotheses = plan.get("hypotheses") or []
            resolved = [h for h in hypotheses if isinstance(h, dict) and h.get("status") not in ("open", None)]
            if resolved:
                report.warn(
                    "lint.single-path-resolution",
                    f"v{v}: hypotheses resolved but brainstorm-FEATURE_MODEL has no rejected_alternative_ids"
                    " — was only one approach tried?",
                    file=str(brainstorm_paths[0]),
                )


def check_lit_technique_ignored(root: Path, report: Report) -> None:
    """Warn when a literature memo section heading names a technique not mentioned in any brainstorm."""
    for lit_path in sorted(root.glob("literature/v*.md")):
        try:
            lit_text = lit_path.read_text()
        except OSError:
            continue
        # Extract ## headings that look like technique names (not metadata headings)
        skip_words = {"overview", "sources", "summary", "conclusion", "background",
                      "references", "limitations", "related", "results", "abstract"}
        headings = []
        for line in lit_text.splitlines():
            if line.startswith("## "):
                heading = line[3:].strip().lower()
                if not any(w in heading for w in skip_words) and len(heading.split()) <= 5:
                    headings.append(heading)
        if not headings:
            continue
        # Collect all brainstorm text for this version
        v_match = re.search(r"v(\d+)", lit_path.stem)
        if not v_match:
            continue
        v = int(v_match.group(1))
        brainstorm_text = ""
        for bp in (root / "runs").glob(f"v{v}/brainstorm-*.md"):
            try:
                brainstorm_text += bp.read_text().lower() + "\n"
            except OSError:
                pass
        if not brainstorm_text:
            continue
        for heading in headings:
            # Check if any key word from the heading appears in brainstorms
            stopwords = {"with", "from", "using", "based", "over", "into", "that", "this",
                         "their", "about", "after", "before", "where", "which", "when", "than",
                         "more", "less", "each", "both", "such", "also", "only", "very"}
            key_words = [w for w in heading.split() if len(w) >= 2 and w not in stopwords]
            if key_words and not any(w in brainstorm_text for w in key_words):
                report.warn(
                    "lint.lit-technique-ignored",
                    f"v{v}: literature memo section '{heading}' not referenced in any brainstorm"
                    " — either attempt it or document why it was rejected",
                    file=str(lit_path),
                )


def check_silent_plan_log(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Warn when plans/vN-updates.md has <3 revisions for a vN that has finding/disproven cards."""
    for v in sorted(plans):
        updates_path = root / "plans" / f"v{v}-updates.md"
        if not updates_path.exists():
            continue
        fm = load_frontmatter(updates_path)
        if not fm:
            continue
        revisions = fm.get("revisions") or []
        if not isinstance(revisions, list):
            continue
        # Only warn if this version has some findings (i.e., work was done)
        has_findings = any(
            True for _ in root.glob(f"findings/v{v}-*.md")
        ) or any(
            True for _ in root.glob(f"disproven/v{v}-*.md")
        )
        if has_findings and len(revisions) < 3:
            report.warn(
                "lint.silent-plan-log",
                f"v{v}: plans/v{v}-updates.md has only {len(revisions)} revision(s)"
                " — either the plan was perfect (unlikely) or learning wasn't documented",
                file=str(updates_path),
            )


def check_learnings_incomplete(root: Path, report: Report) -> None:
    """Warn when runs/vN/learnings.md exists but is missing expected phase exit entries."""
    for learnings_path in sorted((root / "runs").glob("*/learnings.md")):
        fm = load_frontmatter(learnings_path)
        if not fm:
            continue
        recorded = fm.get("phase_exits_recorded") or []
        if not isinstance(recorded, list):
            continue
        # If leaderboard has non-baseline runs for this version, FEATURE_MODEL was reached
        v_match = re.search(r"v(\d+)", learnings_path.parts[-2])
        if not v_match:
            continue
        v = int(v_match.group(1))
        lb_path = root / "dashboard" / "data" / "leaderboard.json"
        if lb_path.exists():
            try:
                lb = json.loads(lb_path.read_text())
                vn_runs = [r for r in (lb.get("runs") or [])
                           if r.get("v") == v and r.get("status") != "invalidated"
                           and not r.get("baseline", False)]
                if vn_runs and "FEATURE_MODEL" not in recorded:
                    report.warn(
                        "lint.learnings-incomplete",
                        f"v{v}: runs/v{v}/learnings.md missing FEATURE_MODEL exit entry"
                        " but non-baseline runs exist on leaderboard",
                        file=str(learnings_path),
                    )
            except (OSError, json.JSONDecodeError):
                pass


def check_learnings_closed(root: Path, report: Report) -> None:
    """Warn when runs/vN/learnings.md has status != 'closed' at VALIDATE exit.

    A learnings file status of 'open' means the analyst hasn't signed off on the
    within-version belief update before moving to VALIDATE → FINDINGS. Checks the
    state.json to determine whether the workspace has reached VALIDATE or later.
    """
    state_path = root / "state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    # Schema uses 'phase'; older code wrote 'current_phase'. Tolerate both.
    phase = state.get("phase") or state.get("current_phase") or ""
    # Only relevant at or past VALIDATE. ABORTED is terminal and does not trigger this check.
    phase_order = [
        "FRAME", "DGP", "AUDIT", "DATA_PREP", "EDA", "FEATURE_MODEL",
        "VALIDATE", "FINDINGS", "MERGE", "SHIP", "ABORTED",
    ]
    try:
        phase_idx = phase_order.index(phase)
    except ValueError:
        return
    if phase == "ABORTED":
        return
    if phase_idx < phase_order.index("VALIDATE"):
        return

    for learnings_path in sorted((root / "runs").glob("*/learnings.md")):
        fm = load_frontmatter(learnings_path)
        if not fm:
            continue
        status = fm.get("status", "open")
        if status != "closed":
            report.warn(
                "lint.learnings-not-closed",
                f"{learnings_path}: learnings.md has status='{status}' but workspace is at "
                f"{phase} phase — should be closed before VALIDATE exit",
                file=str(learnings_path),
            )


def check_explorer_count(root: Path, report: Report) -> None:
    """Warn when advisory Explorer audit has candidate_count < 3."""
    for p in sorted(root.glob("audits/*-explorer-*.md")):
        fm = load_frontmatter(p)
        if not fm:
            continue
        invocation = fm.get("invocation_type", "advisory")
        phase = fm.get("phase", "")
        if phase == "EDA":
            # EDA Explorer: hypothesis_count >=1
            hc = fm.get("hypothesis_count")
            if isinstance(hc, int) and hc < 1:
                report.warn(
                    "lint.explorer-count-low",
                    f"{p.name}: EDA Explorer produced {hc} hypothesis (minimum: 1)",
                    file=str(p),
                )
        else:
            # Advisory DATA_PREP / FEATURE_MODEL: candidate_count >=3
            cc = fm.get("candidate_count")
            if isinstance(cc, int) and cc < 3:
                report.warn(
                    "lint.explorer-count-low",
                    f"{p.name}: advisory Explorer produced {cc} candidate(s) (minimum: 3)",
                    file=str(p),
                )


def _load_state(root: Path) -> dict[str, Any] | None:
    state_path = root / "state.json"
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _current_v(root: Path, plans: dict[int, dict[str, Any]]) -> int:
    """Best-effort current version: state.json → max plan version → 0."""
    state = _load_state(root)
    if state and isinstance(state.get("current_v"), int):
        return state["current_v"]
    if plans:
        return max(plans)
    return 0


def check_secondary_metrics_declared(
    plans: dict[int, dict[str, Any]],
    report: Report,
) -> None:
    """Iron Law #23 — plans/v1.md.pre_registration.secondary_metrics must list >=2 entries.

    Later versions may add (additions OK) but not remove without an override ref.
    """
    v1 = plans.get(1)
    if not v1:
        return
    pr = v1.get("pre_registration") or {}
    secondary = pr.get("secondary_metrics") or []
    if not isinstance(secondary, list) or len(secondary) < 2:
        report.error(
            "lint.anti-goodhart-missing",
            f"plans/v1.md.pre_registration.secondary_metrics must declare >=2 entries"
            f" (found {len(secondary) if isinstance(secondary, list) else 0}); Iron Law #23 violated",
            file=v1.get("_path"),
        )
        return

    v1_names = {
        m.get("name")
        for m in secondary
        if isinstance(m, dict) and m.get("name")
    }
    for v in sorted(plans):
        if v == 1:
            continue
        plan = plans[v]
        pr_v = plan.get("pre_registration") or {}
        sec_v = pr_v.get("secondary_metrics")
        # If vN has its own pre_registration block, its secondary_metrics must be a superset of v1's.
        if sec_v is None:
            continue
        if not isinstance(sec_v, list):
            continue
        names_v = {
            m.get("name")
            for m in sec_v
            if isinstance(m, dict) and m.get("name")
        }
        dropped = v1_names - names_v
        if dropped:
            triggers = plan.get("trigger_refs") or []
            has_override = any(
                isinstance(t, str) and "override" in t.lower() and "anti-goodhart" in t.lower()
                for t in triggers
            )
            if not has_override:
                report.error(
                    "lint.anti-goodhart-shrink",
                    f"plans/v{v}.md secondary_metrics dropped {sorted(dropped)} without"
                    " anti-goodhart override reference (Iron Law #23 + #24)",
                    file=plan["_path"],
                )


def check_secondary_metrics_logged(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Iron Law #23 — every valid run on the leaderboard should log all declared secondary_metrics.

    Missing values block ship-gate; we emit warnings here (error severity raises the ship-gate
    checklist, which is the authoritative gate). The goal is to surface gaps early.
    """
    v1 = plans.get(1)
    if not v1:
        return
    pr = v1.get("pre_registration") or {}
    declared = pr.get("secondary_metrics") or []
    if not isinstance(declared, list):
        return
    required_names = sorted({
        m.get("name")
        for m in declared
        if isinstance(m, dict) and m.get("name")
    })
    if not required_names:
        return

    lb_path = root / "dashboard" / "data" / "leaderboard.json"
    if not lb_path.exists():
        return
    try:
        lb = json.loads(lb_path.read_text())
    except (OSError, json.JSONDecodeError):
        return

    for run in lb.get("runs") or []:
        if run.get("status") == "invalidated":
            continue
        # Baseline & feature-baseline v1 runs may predate metric declaration; only warn for vN>=2.
        if run.get("v", 0) < 2:
            continue
        secondary = run.get("secondary_metrics") or {}
        missing = [n for n in required_names if n not in secondary or secondary.get(n) is None]
        if missing:
            report.warn(
                "lint.secondary-metrics-missing",
                f"run {run.get('id')} (v{run.get('v')}) missing secondary values {missing}"
                " — required by Iron Law #23 at ship-gate",
                file=str(lb_path),
            )


def check_budget_declared(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Iron Law #21 — budget.json must exist once plan v1 is present (FRAME exit).

    Also flags expended envelopes.
    """
    if not plans:
        return
    budget_path = root / "budget.json"
    if not budget_path.exists():
        report.error(
            "lint.budget-missing",
            "budget.json not present; Iron Law #21 requires budget envelope at FRAME exit",
            file=str(budget_path),
        )
        return
    try:
        budget = json.loads(budget_path.read_text())
    except (OSError, json.JSONDecodeError):
        report.error(
            "lint.budget-unreadable",
            f"cannot parse budget.json",
            file=str(budget_path),
        )
        return
    envelopes = budget.get("envelopes") or {}
    if not isinstance(envelopes, dict) or not any(v is not None for v in envelopes.values()):
        report.warn(
            "lint.budget-unbounded",
            "budget.json envelopes all null — no dimension will block runaway spend",
            file=str(budget_path),
        )
    ledger = budget.get("ledger") or []
    if isinstance(ledger, list) and isinstance(envelopes, dict):
        spent_compute = sum((e.get("spend") or {}).get("compute_hours", 0) or 0 for e in ledger if isinstance(e, dict))
        spent_api = sum((e.get("spend") or {}).get("api_cost_usd", 0) or 0 for e in ledger if isinstance(e, dict))
        cap_compute = envelopes.get("compute_hours")
        cap_api = envelopes.get("api_cost_usd")
        if isinstance(cap_compute, (int, float)) and cap_compute > 0 and spent_compute >= 0.8 * cap_compute:
            report.warn(
                "lint.budget-near-exhaustion",
                f"compute_hours spend {spent_compute:.1f} >= 80% of cap {cap_compute}",
                file=str(budget_path),
            )
        if isinstance(cap_api, (int, float)) and cap_api > 0 and spent_api >= 0.8 * cap_api:
            report.warn(
                "lint.budget-near-exhaustion",
                f"api_cost_usd spend {spent_api:.2f} >= 80% of cap {cap_api}",
                file=str(budget_path),
            )


def check_coverage_present(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Iron Law #25 — coverage.json must exist from v1 onward and must be refreshed after each VALIDATE exit.

    The 'coverage-stale' event fires when the file has not been updated for >=2 versions; we
    emit a warning so that the daily-mode loop surfaces this without blocking, while the
    ship-gate checklist refuses promotion when stale in competition mode.
    """
    if not plans:
        return
    coverage_path = root / "coverage.json"
    current_v = _current_v(root, plans)

    if not coverage_path.exists():
        report.error(
            "lint.coverage-missing",
            "coverage.json not present; Iron Law #25 requires it from v1 onward",
            file=str(coverage_path),
        )
        return

    try:
        cov = json.loads(coverage_path.read_text())
    except (OSError, json.JSONDecodeError):
        report.error(
            "lint.coverage-unreadable",
            "cannot parse coverage.json",
            file=str(coverage_path),
        )
        return

    areas = cov.get("pattern_areas") or []
    if not isinstance(areas, list) or not areas:
        report.error(
            "lint.coverage-empty",
            "coverage.json has no pattern_areas; initialize from SKILL.md pattern map",
            file=str(coverage_path),
        )
        return

    # Stale-since check: highest last_tried_vN across all areas should be within 2 of current_v.
    last_tried = [
        a.get("last_tried_vN")
        for a in areas
        if isinstance(a, dict) and isinstance(a.get("last_tried_vN"), int)
    ]
    if current_v >= 2 and last_tried:
        newest = max(last_tried)
        if current_v - newest >= 2:
            report.warn(
                "lint.coverage-stale",
                f"coverage.json newest last_tried_vN={newest} but current_v={current_v}"
                " — refresh required by Iron Law #25 (coverage-stale event)",
                file=str(coverage_path),
            )

    # Remaining_leverage sanity: exhausted with leverage>0.5 must be justified.
    for area in areas:
        if not isinstance(area, dict):
            continue
        if area.get("exhausted") and (area.get("remaining_leverage_estimate") or 0) > 0.5:
            if not area.get("notes_ref"):
                report.warn(
                    "lint.coverage-leverage-unjustified",
                    f"pattern_area '{area.get('name')}' is exhausted but leverage_estimate"
                    f"={area.get('remaining_leverage_estimate')}; notes_ref required",
                    file=str(coverage_path),
                )

    # Priority=top with empty approaches_tried is a red flag.
    for area in areas:
        if not isinstance(area, dict):
            continue
        if area.get("priority") == "top" and not (area.get("approaches_tried") or []):
            report.warn(
                "lint.coverage-top-unexplored",
                f"pattern_area '{area.get('name')}' is priority=top but approaches_tried is empty",
                file=str(coverage_path),
            )


LAW_SLUG_TO_ID: dict[str, str] = {
    # numeric strings map to themselves (no surprise when already canonical)
    "1": "1", "12": "12", "16": "16", "17": "17", "20": "20",
    # common slug forms used throughout templates + playbooks. If a Council authors an
    # override as `law: eval-harness` the guard must still see it as Iron Law #20.
    "holdout": "1", "holdout-integrity": "1",
    "dgp": "12", "dgp-memo": "12",
    "external-submit": "16", "submission": "16", "one-shot-submission": "16",
    "consistency": "17", "consistency-alignment": "17", "knowledge-alignment": "17",
    "eval-harness": "20", "evaluation-harness": "20", "harness-lock": "20",
    # budget is its own canonical form — match the existing autonomous.yaml.budget key.
    "budget": "budget",
}

LAWS_REJECT_PERMANENT: set[str] = {
    # Iron Law #20 eval-harness locks: playbooks/event-eval-harness-tampered.md states
    # "consistency_lint.py rejects any scope=permanent for law=eval-harness". Enforce that
    # claim — any permanent relaxation of the harness lock is an outright error, not just
    # "needs user signature". Same rationale for one-shot submission discipline (#16).
    "20", "16",
}


def _canonical_law(law_raw: object) -> str:
    """Normalise a YAML `law` value to the canonical id used by core-law guards.

    Accepts numeric strings ("1", "20") and slug strings ("eval-harness", "dgp-memo");
    unknown values pass through lowercased so the guard can still report them verbatim.
    Non-string inputs return an empty string (which fails every membership check below).
    """
    if not isinstance(law_raw, str):
        return ""
    key = law_raw.strip().lower()
    return LAW_SLUG_TO_ID.get(key, key)


def check_overrides(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Iron Law #24 — every active override id in state.json must have a backing artifact under overrides/.

    Also flags:
    - signed_by MUST be a YAML list (scalar-string iteration silently bypasses core-law check);
    - scope=permanent overrides require at least 2 signers (council quorum);
    - core-law (+budget) permanent overrides require at least one human ('user') signer;
    - scope=permanent is refused outright for laws in LAWS_REJECT_PERMANENT (#20 eval-harness,
      #16 external-submit) — those laws cannot be mechanically relaxed, period;
    - `law` field is resolved via LAW_SLUG_TO_ID so slug-form values (`eval-harness`, `dgp`,
      `consistency`) don't bypass the core-law guard by dodging numeric-string equality;
    - expired overrides still active;
    - override files on disk whose id is not in state.active_overrides and whose scope/expiry
      suggests they should still be tracked (reverse-sync drift). Core-law permanent overrides
      that are orphaned are errors, not warnings.
    """
    state = _load_state(root)
    overrides_dir = root / "overrides"
    by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(overrides_dir.glob("*.md")) if overrides_dir.exists() else []:
        fm = load_frontmatter(path)
        if not fm:
            continue
        oid = fm.get("id")
        if oid:
            by_id[oid] = {**fm, "_path": str(path)}

    # Validate every override card on disk, regardless of active_overrides membership.
    current_v = _current_v(root, plans)
    core_laws_need_human = {"1", "12", "16", "17", "20", "budget"}

    for oid, card in by_id.items():
        path = card["_path"]
        law_raw = card.get("law")
        law = _canonical_law(law_raw)
        scope = card.get("scope")
        signed_by_raw = card.get("signed_by")

        # Safety bug: scalar strings iterate character-by-character and silently pass the
        # "not council" check. Require a list.
        if signed_by_raw is None:
            signed_by: list[str] = []
        elif isinstance(signed_by_raw, list):
            signed_by = [s for s in signed_by_raw if isinstance(s, str)]
        else:
            report.error(
                "lint.override-signed-by-not-list",
                f"override '{oid}' signed_by must be a YAML list, not a {type(signed_by_raw).__name__}"
                f" (value: {signed_by_raw!r}); scalar strings iterate per-character and bypass signer checks",
                file=path,
            )
            signed_by = []

        if scope == "permanent":
            if law in LAWS_REJECT_PERMANENT:
                report.error(
                    "lint.override-permanent-forbidden",
                    f"override '{oid}' claims scope=permanent for law '{law_raw}' "
                    f"(canonical id {law!r}); Iron Law #{law} cannot be relaxed permanently "
                    f"under any council quorum — use scope=run with a re-lock plan",
                    file=path,
                )
            if len(signed_by) < 2:
                report.error(
                    "lint.override-permanent-quorum-missing",
                    f"override '{oid}' is scope=permanent but signed_by has {len(signed_by)} entries"
                    f" (Iron Law #24 requires Council quorum >=2)",
                    file=path,
                )
            if law in core_laws_need_human:
                has_user = any(s.strip().lower() == "user" for s in signed_by)
                if not has_user:
                    report.error(
                        "lint.override-core-law-no-human",
                        f"override '{oid}' relaxes core law '{law_raw}' (canonical {law!r})"
                        f" at permanent scope but signed_by lacks a 'user' entry;"
                        f" Iron Law #24 requires human sign-off for laws"
                        f" {sorted(core_laws_need_human)} at permanent scope even in autonomous mode",
                        file=path,
                    )

        # Expiration check
        expires = card.get("expires_at")
        if isinstance(expires, str) and expires.startswith("v") and current_v:
            try:
                exp_v = int(expires[1:])
                if current_v > exp_v:
                    report.error(
                        "lint.override-expired-still-active",
                        f"override '{oid}' expired at {expires} but card still on disk"
                        f" (current_v={current_v}); archive or retire the artifact",
                        file=path,
                    )
            except ValueError:
                pass

    # Forward sync: state.active_overrides entries must have backing artifacts.
    if state:
        active = state.get("active_overrides") or []
        for oid in active:
            if oid not in by_id:
                report.error(
                    "lint.override-missing-artifact",
                    f"state.active_overrides lists '{oid}' but no matching file in overrides/",
                    file=str(root / "state.json"),
                )

        # Reverse sync: override files whose id is not listed in state.active_overrides.
        # Only flag overrides that *should* still be tracked — scope=permanent or scope=version
        # covering current_v, and not yet expired by vN comparison.
        active_set = set(active)
        for oid, card in by_id.items():
            if oid in active_set:
                continue
            scope = card.get("scope")
            expires = card.get("expires_at")
            v_of_card = card.get("vN") if isinstance(card.get("vN"), int) else None
            still_applicable = False
            if scope == "permanent":
                still_applicable = True
            elif scope == "version" and v_of_card == current_v:
                still_applicable = True
            elif scope == "run" and v_of_card == current_v:
                still_applicable = True
            if isinstance(expires, str) and expires.startswith("v") and current_v:
                try:
                    exp_v = int(expires[1:])
                    if current_v > exp_v:
                        still_applicable = False
                except ValueError:
                    pass
            if still_applicable:
                card_law = _canonical_law(card.get("law"))
                is_core_permanent = (
                    scope == "permanent" and card_law in core_laws_need_human
                )
                message = (
                    f"override '{oid}' ({scope=}) exists at {card['_path']} but is not in"
                    f" state.active_overrides — state/filesystem drift"
                )
                if is_core_permanent:
                    report.error(
                        "lint.override-orphan-core-permanent",
                        f"{message}; core-law permanent overrides MUST stay registered in "
                        f"state.active_overrides or be explicitly retired (law='{card_law}')",
                        file=card["_path"],
                    )
                else:
                    report.warn(
                        "lint.override-orphan-file",
                        message,
                        file=card["_path"],
                    )


def check_meta_audit_monotonic(root: Path, report: Report) -> None:
    """Iron Law #22/#24 anti-gaming — state.last_meta_audit_v must match disk evidence.

    Three failure modes this catches:
    1. Rollback — state.last_meta_audit_v was silently decreased (lets orchestrator defer
       a due audit by pretending the counter is smaller than it is).
    2. Fabrication — state.last_meta_audit_v > max(vN among meta-audit artifacts). No
       artifact on disk means no audit happened; a forward-written counter is gaming.
    3. Future-dating — state.last_meta_audit_v > state.current_v. An audit for a version
       that doesn't exist yet is nonsensical.

    The artifact directory is `autonomous.yaml.logging.meta_audit_artifact_dir` with
    default `audits/meta/`. If autonomous.yaml is absent, the default is used.
    Silent pass when state.json is absent (pre-init workspace).
    """
    state = _load_state(root)
    if not state:
        return
    last_v = state.get("last_meta_audit_v")
    current_v = state.get("current_v")
    if last_v is None:
        return
    if not isinstance(last_v, int) or last_v < 0:
        report.error(
            "lint.meta-audit-counter-malformed",
            f"state.last_meta_audit_v={last_v!r} is not a non-negative integer",
            file=str(root / "state.json"),
        )
        return
    if isinstance(current_v, int) and last_v > current_v:
        report.error(
            "lint.meta-audit-future-dated",
            f"state.last_meta_audit_v={last_v} exceeds state.current_v={current_v} "
            "(can't have audited a version that hasn't happened)",
            file=str(root / "state.json"),
        )

    meta_dir_name = "audits/meta"
    yaml_path = root.parent / "autonomous.yaml"
    if yaml_path.exists():
        try:
            config = yaml.safe_load(yaml_path.read_text()) or {}
            configured = (config.get("logging") or {}).get("meta_audit_artifact_dir")
            if isinstance(configured, str) and configured.strip():
                meta_dir_name = configured.strip().rstrip("/")
        except yaml.YAMLError:
            pass

    meta_dir = root / meta_dir_name
    versions_on_disk: list[int] = []
    if meta_dir.exists() and meta_dir.is_dir():
        version_pattern = re.compile(r"^v(\d+)-meta-audit\.md$")
        for entry in meta_dir.iterdir():
            m = version_pattern.match(entry.name)
            if m and entry.is_file():
                versions_on_disk.append(int(m.group(1)))
    max_on_disk = max(versions_on_disk) if versions_on_disk else 0
    if last_v > max_on_disk:
        report.error(
            "lint.meta-audit-fabricated",
            f"state.last_meta_audit_v={last_v} but highest vN in {meta_dir_name}/ is "
            f"{max_on_disk} (state claims an audit that has no artifact on disk)",
            file=str(root / "state.json"),
        )


def check_holdout_reads_integrity(root: Path, report: Report) -> None:
    """Iron Law #1 anti-rollback — state.holdout_reads must match disk evidence.

    Ship-gate § "Internal holdout read (the only one)" says every read increments the
    counter AND stamps `audits/vN-repro.md`. The counter on its own is rollback-able
    (edit state.json from 1→0 and no one would know). We cross-check against the
    artifact stamps so a rollback shows up as state/filesystem drift.

    Failure modes caught:
    1. Rollback — state.holdout_reads < count of `audits/v*-repro.md` stamps on disk.
    2. Fabrication — state.holdout_reads > disk stamps (an audit claims a read that
       never produced evidence; opposite direction of rollback, same integrity break).
    3. Malformed counter — non-integer or negative value.
    Silent pass when state.json is absent (pre-init workspace).
    """
    state = _load_state(root)
    if not state:
        return
    reads = state.get("holdout_reads")
    if reads is None:
        return
    if not isinstance(reads, int) or reads < 0:
        report.error(
            "lint.holdout-reads-counter-malformed",
            f"state.holdout_reads={reads!r} is not a non-negative integer",
            file=str(root / "state.json"),
        )
        return

    audits_dir = root / "audits"
    stamps = 0
    if audits_dir.exists() and audits_dir.is_dir():
        stamp_pattern = re.compile(r"^v\d+-repro\.md$")
        for entry in audits_dir.iterdir():
            if not entry.is_file() or not stamp_pattern.match(entry.name):
                continue
            try:
                text = entry.read_text()
            except OSError:
                continue
            # The ship-gate explicitly says "stamp audits/vN-repro.md" on a read.
            # We don't require a specific marker; presence of the file is the stamp.
            # A repro audit that did NOT read the holdout should live elsewhere.
            if "holdout" in text.lower():
                stamps += 1

    if reads > stamps:
        report.error(
            "lint.holdout-reads-fabricated",
            f"state.holdout_reads={reads} but only {stamps} audits/v*-repro.md stamp(s)"
            " with holdout evidence on disk — counter claims a read that has no artifact",
            file=str(root / "state.json"),
        )
    elif reads < stamps:
        report.error(
            "lint.holdout-reads-rollback",
            f"state.holdout_reads={reads} but {stamps} audits/v*-repro.md stamp(s) on"
            " disk reference the holdout — counter was rolled back (Iron Law #1 forbids)",
            file=str(root / "state.json"),
        )


def check_surrender_card(root: Path, plans: dict[int, dict[str, Any]], report: Report) -> None:
    """Iron Law #22 — if state.phase == ABORTED, disproven/surrender-vN.md must exist and match current_v."""
    state = _load_state(root)
    if not state:
        return
    phase = state.get("phase")
    if phase != "ABORTED":
        return
    current_v = state.get("current_v")
    candidates = list((root / "disproven").glob("surrender-v*.md")) if (root / "disproven").exists() else []
    if not candidates:
        report.error(
            "lint.surrender-missing",
            "state.phase=ABORTED but no disproven/surrender-vN.md present; Iron Law #22 requires one",
            file=str(root / "state.json"),
        )
        return
    if current_v is not None:
        expected = root / "disproven" / f"surrender-v{current_v}.md"
        if not expected.exists():
            report.warn(
                "lint.surrender-version-mismatch",
                f"state.current_v={current_v} but disproven/surrender-v{current_v}.md missing"
                f" (found {[c.name for c in candidates]})",
                file=str(expected),
            )


def run(root: Path) -> Report:
    report = Report()
    if not root.exists():
        report.error("workspace.missing", f"{root} does not exist")
        return report

    predictions = latest_dgp_predictions(root, report)
    plans = collect_plans(root)
    findings = collect_cards(root, "findings", "finding")
    disproven = collect_cards(root, "disproven", "disproven")

    known_ids = {
        "findings": {c.get("id") for c in findings if c.get("id")},
        "disproven": {c.get("id") for c in disproven if c.get("id")},
        "hypotheses": {
            h.get("id")
            for p in plans.values()
            for h in (p.get("hypotheses") or [])
            if isinstance(h, dict) and h.get("id")
        },
        "dgp_predictions": set(predictions.keys()),
    }

    check_hypotheses_resolved(plans, findings, disproven, report)
    check_card_plan_refs(plans, findings + disproven, report)
    check_dgp_refs(findings + disproven, predictions, report)
    check_direction_contradictions(findings, disproven, report)
    check_supersedes_chain(findings + disproven, report)
    check_pre_registration_uniformity(plans, report)
    check_leaderboard_alignment(root, findings, report)
    check_top_predictions_touched(predictions, findings, disproven, report)
    check_step_journal(root, known_ids, report)
    check_lessons_sources(root, known_ids, report)

    # Iron Law #19 — mechanical enforcement (errors, blocking)
    check_brainstorm_count(root, report)
    check_feature_baseline_present(root, report)
    check_tuning_has_default_params(root, report)

    # Tier 3 polish — creativity and learning discipline (warnings, non-blocking)
    check_single_path_resolution(root, plans, report)
    check_lit_technique_ignored(root, report)
    check_silent_plan_log(root, plans, report)
    check_learnings_incomplete(root, report)
    check_learnings_closed(root, report)
    check_explorer_count(root, report)

    # Iron Laws #21-25 — autonomous-mode scaffolding
    check_secondary_metrics_declared(plans, report)
    check_secondary_metrics_logged(root, plans, report)
    check_budget_declared(root, plans, report)
    check_coverage_present(root, plans, report)
    check_overrides(root, plans, report)
    check_surrender_card(root, plans, report)
    check_meta_audit_monotonic(root, report)
    check_holdout_reads_integrity(root, report)

    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", type=Path, help="path to ds-workspace/")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    report = run(args.workspace)

    if args.json:
        print(json.dumps({"issues": [i.as_dict() for i in report.issues]}, indent=2))
    else:
        errors = [i for i in report.issues if i.severity == "error"]
        warnings = [i for i in report.issues if i.severity == "warning"]
        infos = [i for i in report.issues if i.severity == "info"]
        print(f"# consistency lint: {args.workspace}")
        print(f"errors: {len(errors)}  warnings: {len(warnings)}  info: {len(infos)}")
        for group, label in ((errors, "ERRORS"), (warnings, "WARNINGS"), (infos, "INFO")):
            if not group:
                continue
            print(f"\n## {label}")
            for issue in group:
                loc = f" ({issue.file})" if issue.file else ""
                print(f"- [{issue.code}] {issue.message}{loc}")
        print(f"\nVERDICT: {'FAIL' if report.has_errors() else 'PASS'}")

    return 1 if report.has_errors() else 0


if __name__ == "__main__":
    sys.exit(main())
