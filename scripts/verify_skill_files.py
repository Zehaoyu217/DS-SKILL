#!/usr/bin/env python3
"""Verify required skill files exist and have minimal structure."""
from __future__ import annotations
import pathlib, re, sys, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

REQUIRED = [
    "SKILL.md", "iron-laws.md", "loop-state-machine.md",
    "workspace-layout.md", "dashboard-spec.md",
    "personas/skeptic.md", "personas/validation-auditor.md",
    "personas/statistician.md", "personas/explorer.md",
    "personas/literature-scout.md", "personas/engineer.md",
    "personas/domain-expert.md",
    "playbooks/phase-frame.md", "playbooks/phase-dgp.md",
    "playbooks/phase-audit.md", "playbooks/phase-data-prep.md",
    "playbooks/phase-eda.md", "playbooks/phase-feature-model.md",
    "playbooks/phase-validate.md", "playbooks/phase-findings.md",
    "playbooks/phase-merge.md",
    "playbooks/event-leakage-found.md",
    "playbooks/event-assumption-disproven.md",
    "playbooks/event-metric-plateau.md",
    "playbooks/event-cv-holdout-drift.md",
    "playbooks/event-novel-modeling-flag.md",
    "playbooks/event-covariate-shift.md",
    "playbooks/event-suspicious-lift.md",
    "playbooks/event-submission-drift.md",
    "playbooks/event-eval-harness-tampered.md",
    "templates/plan-vN.md", "templates/plan-updates-vN.md",
    "templates/brainstorm-vN.md",
    "templates/tuning-plan-vN.md",
    "templates/learnings-vN.md",
    "templates/persona-debate.md",
    "templates/finding-card.md",
    "templates/disproven-card.md", "templates/literature-memo.md",
    "templates/dgp-memo.md",
    "templates/step-journal.md", "templates/lessons.md",
    "templates/sandbox-vN.ipynb",
    "templates/state.schema.json", "templates/leaderboard.schema.json",
    "checklists/leakage-audit.md", "checklists/cv-scheme-decision.md",
    "checklists/assumption-tests.md", "checklists/reproducibility.md",
    "checklists/ship-gate.md",
    "checklists/encoding-audit.md",
    "checklists/adversarial-validation.md",
    "checklists/narrative-audit.md",
    "checklists/submission-format.md",
    "checklists/model-diagnostics.md",
    "checklists/experiment-tracking.md",
    "scripts/adversarial_validation.py",
    "scripts/check_submission_format.py",
    "scripts/consistency_lint.py",
    "scripts/tracker_log.py",
    "scripts/hash_eval_harness.py",
    "scripts/log_run_commit.sh",
    "scripts/leakage_grep.sh",
    "playbooks/collab-brainstorm.md",
    "templates/user-guidance.md",
    "templates/research-program.md",
    "dashboard-template/index.html",
    "dashboard-template/assets/styles.css",
    "dashboard-template/assets/app.js",
    "dashboard-template/assets/charts.js",
    "server/serve_dashboard.py",
    "slash/ds.md",
    "slash/ds-init.md",
    "scripts/init_workspace.py",
    "scripts/hooks/ds-state-surface.sh",
    "scripts/hooks/ds-phase-check.sh",
    "README.md",
    # ds-patterns sub-skills
    "ds-patterns/data-quality.md",
    "ds-patterns/feature-engineering.md",
    "ds-patterns/model-selection.md",
    "ds-patterns/ensemble.md",
    "ds-patterns/ml-classification.md",
    "ds-patterns/idea-research.md",
]

FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

def check_skill_frontmatter(p: pathlib.Path) -> list[str]:
    text = p.read_text()
    m = FRONTMATTER.match(text)
    if not m:
        return [f"{p.name}: missing YAML frontmatter"]
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return [f"{p.name}: invalid YAML frontmatter ({e})"]
    errs = []
    for k in ("name", "description"):
        if not fm.get(k):
            errs.append(f"{p.name}: frontmatter missing '{k}'")
    return errs

def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"MISSING: {rel}")
    skill_md = ROOT / "SKILL.md"
    if skill_md.exists():
        errors.extend(check_skill_frontmatter(skill_md))
    if errors:
        print("\n".join(errors))
        return 1
    print("OK: all required files present")
    return 0

if __name__ == "__main__":
    sys.exit(main())
