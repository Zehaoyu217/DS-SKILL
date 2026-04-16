# tests/test_ds_patterns.py
"""Schema validator for ds-patterns/ sub-skill files."""
from __future__ import annotations
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATTERNS_DIR = ROOT / "ds-patterns"

REQUIRED_FILES = [
    "data-quality.md",
    "feature-engineering.md",
    "model-selection.md",
    "ensemble.md",
    "ml-classification.md",
]

REQUIRED_FIELDS = [
    "**Worth exploring when:**",
    "**What to try:**",
    "**Ceiling signal:**",
    "**Watch out for:**",
]


def test_pattern_files_exist() -> None:
    for fname in REQUIRED_FILES:
        p = PATTERNS_DIR / fname
        assert p.exists(), f"Missing pattern file: ds-patterns/{fname}"


def test_each_file_has_complete_pattern_entries() -> None:
    for fname in REQUIRED_FILES:
        p = PATTERNS_DIR / fname
        if not p.exists():
            continue
        text = p.read_text()
        entries = re.split(r"\n## ", text)
        pattern_entries = [e for e in entries[1:] if e.strip()]
        assert pattern_entries, (
            f"{fname}: no pattern entries found (need at least one ## heading)"
        )
        for entry in pattern_entries:
            for field in REQUIRED_FIELDS:
                assert field in entry, (
                    f"{fname}: pattern '{entry[:50].strip()}...' missing field '{field}'"
                )


def test_no_deprecated_evidence_field() -> None:
    """Evidence field was removed from schema — Watch out for accumulates lessons instead."""
    for fname in REQUIRED_FILES:
        p = PATTERNS_DIR / fname
        if not p.exists():
            continue
        text = p.read_text()
        assert "**Evidence:**" not in text, (
            f"{fname}: contains deprecated '**Evidence:**' — use '**Watch out for:**' instead"
        )
