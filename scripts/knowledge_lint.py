#!/usr/bin/env python3
"""Knowledge-base linter for a ds-workspace.

Audits ds-workspace/knowledge-base.md for staleness, unexplored variables,
unconsumed model-synthesis patches, and segment gaps. Output is warnings
only — this linter never blocks a phase.

Exit codes:
    0  ok (warnings may still be printed)
    2  workspace missing or knowledge-base.md unparseable

Usage:
    python knowledge_lint.py <ds-workspace-root>
    python knowledge_lint.py ds-workspace --json > report.json
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


YAML_FENCE_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
SECTION_RE = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
LAST_REVIEWED_RE = re.compile(r"^last_reviewed:\s*v(\d+)", re.MULTILINE | re.IGNORECASE)
VERSION_TAG_RE = re.compile(r"v(\d+)")
OPENED_RE = re.compile(r"opened\s+v(\d+)", re.IGNORECASE)

STALENESS_VERSIONS = 5
HYPOTHESIS_STALENESS_VERSIONS = 3
OPEN_Q_STALENESS_VERSIONS = 5


@dataclass
class Issue:
    severity: str
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

    def warn(self, code: str, message: str, file: str | None = None) -> None:
        self.issues.append(Issue("warning", code, message, file))

    def info(self, code: str, message: str, file: str | None = None) -> None:
        self.issues.append(Issue("info", code, message, file))

    def as_dict(self) -> dict[str, Any]:
        return {
            "issues": [i.as_dict() for i in self.issues],
            "counts": {
                "warning": sum(1 for i in self.issues if i.severity == "warning"),
                "info": sum(1 for i in self.issues if i.severity == "info"),
            },
        }


def _current_version(root: Path) -> int:
    try:
        state = json.loads((root / "state.json").read_text())
    except (OSError, json.JSONDecodeError):
        return 0
    value = state.get("current_version") or state.get("version") or 0
    if isinstance(value, str):
        match = VERSION_TAG_RE.search(value)
        return int(match.group(1)) if match else 0
    if isinstance(value, int):
        return value
    return 0


def _load_kb(
    root: Path,
) -> tuple[str, list[dict[str, Any]], list[tuple[int, str, int | None]]]:
    """Return (full_text, yaml_blocks, section_records).

    `section_records` is a list of (section_number, title, last_reviewed_v)
    where `last_reviewed_v` is None when the stamp is missing.
    """
    kb_path = root / "knowledge-base.md"
    text = kb_path.read_text()

    yaml_blocks: list[dict[str, Any]] = []
    for match in YAML_FENCE_RE.finditer(text):
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(data, dict):
            yaml_blocks.append(data)

    sections: list[tuple[int, str, int | None]] = []
    section_spans = list(SECTION_RE.finditer(text))
    for idx, header in enumerate(section_spans):
        number = int(header.group(1))
        title = header.group(2).strip()
        start = header.end()
        end = (
            section_spans[idx + 1].start()
            if idx + 1 < len(section_spans)
            else len(text)
        )
        body = text[start:end]
        lr = LAST_REVIEWED_RE.search(body)
        last_reviewed = int(lr.group(1)) if lr else None
        sections.append((number, title, last_reviewed))
    return text, yaml_blocks, sections


def _find_block(
    yaml_blocks: list[dict[str, Any]], key: str
) -> list[dict[str, Any]] | None:
    for block in yaml_blocks:
        value = block.get(key)
        if isinstance(value, list):
            return value
    return None


def check_sections_stale(
    sections: list[tuple[int, str, int | None]],
    current_v: int,
    report: Report,
) -> None:
    if current_v <= 0:
        return
    threshold = max(current_v - STALENESS_VERSIONS, 0)
    for number, title, last_reviewed in sections:
        # §8 "Open questions" is a rolling list — per-item "opened vN" stamps
        # replace the section-level stamp. Skip it from the staleness check.
        if title.lower().startswith("open questions"):
            continue
        if last_reviewed is None:
            report.warn(
                "kb.section-no-last-reviewed",
                f"§{number} {title}: missing last_reviewed stamp",
                file="knowledge-base.md",
            )
        elif last_reviewed < threshold:
            report.warn(
                "kb.section-stale",
                f"§{number} {title}: last_reviewed=v{last_reviewed} "
                f"(current=v{current_v}, threshold=v{threshold})",
                file="knowledge-base.md",
            )


def check_variables_unexplored(
    yaml_blocks: list[dict[str, Any]], report: Report
) -> None:
    variables = _find_block(yaml_blocks, "variables")
    if variables is None:
        return
    in_basis_unexplored: list[str] = []
    out_of_basis_unexplored: list[str] = []
    for var in variables:
        if not isinstance(var, dict):
            continue
        name = var.get("name", "<unnamed>")
        explored = var.get("explored") or []
        if explored:
            continue
        if var.get("in_feature_basis") is True:
            in_basis_unexplored.append(name)
        else:
            out_of_basis_unexplored.append(name)
    if in_basis_unexplored:
        report.warn(
            "kb.variables-in-basis-unexplored",
            f"{len(in_basis_unexplored)} in-basis variables have explored=[]: "
            f"{', '.join(in_basis_unexplored[:10])}"
            + ("..." if len(in_basis_unexplored) > 10 else ""),
            file="knowledge-base.md",
        )
    if out_of_basis_unexplored:
        report.info(
            "kb.variables-not-in-basis-unexplored",
            f"{len(out_of_basis_unexplored)} non-basis variables have "
            f"explored=[] (EDA candidates): "
            f"{', '.join(out_of_basis_unexplored[:10])}"
            + ("..." if len(out_of_basis_unexplored) > 10 else ""),
            file="knowledge-base.md",
        )


def _coerce_vN(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = VERSION_TAG_RE.search(value)
        return int(match.group(1)) if match else None
    return None


def check_hypotheses_stale(
    yaml_blocks: list[dict[str, Any]],
    current_v: int,
    report: Report,
) -> None:
    hypotheses = _find_block(yaml_blocks, "hypotheses")
    if hypotheses is None or current_v <= 0:
        return
    threshold = max(current_v - HYPOTHESIS_STALENESS_VERSIONS, 0)
    for hyp in hypotheses:
        if not isinstance(hyp, dict):
            continue
        if hyp.get("status") != "pending":
            continue
        hid = hyp.get("id", "<unnamed>")
        last_v = _coerce_vN(hyp.get("last_checked_vN"))
        if last_v is None:
            report.warn(
                "kb.hypothesis-no-last-checked",
                f"{hid} is pending but has no last_checked_vN",
                file="knowledge-base.md",
            )
        elif last_v < threshold:
            report.warn(
                "kb.hypothesis-stale",
                f"{hid} pending since v{last_v} "
                f"(current=v{current_v}, threshold=v{threshold})",
                file="knowledge-base.md",
            )


def check_segments_stuck(
    yaml_blocks: list[dict[str, Any]], report: Report
) -> None:
    segments = _find_block(yaml_blocks, "segments")
    if segments is None:
        return
    flat: list[str] = []
    regressing: list[str] = []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        trend = seg.get("trend_last_k_versions", "")
        name = seg.get("name", "<unnamed>")
        if trend == "flat":
            flat.append(name)
        elif trend == "regressing":
            regressing.append(name)
    if regressing:
        report.warn(
            "kb.segment-regressing",
            f"segments regressing: {', '.join(regressing)} "
            f"— surface in next coach note",
            file="knowledge-base.md",
        )
    if flat:
        report.warn(
            "kb.segment-flat",
            f"segments flat: {', '.join(flat)} "
            f"— candidate for targeted investigation",
            file="knowledge-base.md",
        )


def check_open_questions_stale(
    text: str, current_v: int, report: Report
) -> None:
    if current_v <= 0:
        return
    match = re.search(
        r"## 8\. Open questions.*?\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return
    threshold = max(current_v - OPEN_Q_STALENESS_VERSIONS, 0)
    stale: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("- [ ]"):
            continue
        m2 = OPENED_RE.search(stripped)
        if not m2:
            continue
        if int(m2.group(1)) < threshold:
            stale.append(stripped)
    if stale:
        report.warn(
            "kb.open-questions-stale",
            f"{len(stale)} open questions older than v{threshold} "
            f"(first: {stale[0][:80]})",
            file="knowledge-base.md",
        )


def check_unconsumed_synthesis_patches(
    root: Path,
    sections: list[tuple[int, str, int | None]],
    report: Report,
) -> None:
    audits = sorted(root.glob("audits/v*-model-synthesis.md"))
    recent = audits[-3:]
    if not recent:
        return
    section_lookup = {num: lr for num, _, lr in sections}
    for audit in recent:
        try:
            text = audit.read_text()
        except OSError:
            continue
        body_match = re.search(
            r"(?:^|\n)## 7\. Proposed KB patches(.*?)(?=\n## |\Z)",
            text,
            re.DOTALL,
        )
        if not body_match:
            continue
        patch_lines = [
            line.strip()
            for line in body_match.group(1).splitlines()
            if line.strip().startswith("- §")
        ]
        if not patch_lines:
            continue
        audit_v_match = re.search(r"v(\d+)-model-synthesis", audit.name)
        if not audit_v_match:
            continue
        audit_v = int(audit_v_match.group(1))
        for line in patch_lines:
            target_match = re.match(r"- §(\d+)", line)
            if not target_match:
                continue
            target_section = int(target_match.group(1))
            last_reviewed = section_lookup.get(target_section)
            if last_reviewed is None or last_reviewed < audit_v:
                report.warn(
                    "kb.unconsumed-synthesis-patch",
                    f"v{audit_v} synthesis proposes §{target_section} patch "
                    f"not reflected in KB "
                    f"(last_reviewed=v{last_reviewed if last_reviewed is not None else 'none'})",
                    file=audit.name,
                )


def run(root: Path) -> Report:
    report = Report()
    kb_path = root / "knowledge-base.md"
    if not kb_path.exists():
        report.warn(
            "kb.missing",
            "knowledge-base.md not found — run /ds-kb init to bootstrap",
            file="knowledge-base.md",
        )
        return report
    try:
        text, yaml_blocks, sections = _load_kb(root)
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"could not read knowledge-base.md: {exc}") from exc
    current_v = _current_version(root)
    check_sections_stale(sections, current_v, report)
    check_variables_unexplored(yaml_blocks, report)
    check_hypotheses_stale(yaml_blocks, current_v, report)
    check_segments_stuck(yaml_blocks, report)
    check_open_questions_stale(text, current_v, report)
    check_unconsumed_synthesis_patches(root, sections, report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workspace", type=Path)
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    args = ap.parse_args()

    root = args.workspace
    if not root.is_dir():
        print(f"workspace not found: {root}", file=sys.stderr)
        return 2
    try:
        report = run(root)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        if not report.issues:
            print("knowledge-base.md: GREEN — no warnings")
        else:
            print(f"knowledge-base.md: {len(report.issues)} issue(s)")
            for issue in report.issues:
                prefix = issue.severity.upper()
                location = f" ({issue.file})" if issue.file else ""
                print(f"  [{prefix}] {issue.code}: {issue.message}{location}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
