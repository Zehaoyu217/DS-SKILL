# Step Journal — v{N}

> Append-only log of non-trivial decisions and chain-of-thought during v{N}.
> New entries at the bottom; never edit or delete past entries.
> `scripts/consistency_lint.py` scans this file to detect decisions that contradict prior findings or the DGP memo.

## Session start (fill this table at the top of every new Claude Code session)

| Question | Answer |
|---|---|
| Where am I? (phase + version) | |
| Last action completed | |
| Goal for this session | |
| Active blockers | |
| Next gate artifact required | |

> How to fill: read `state.json` for phase/version, tail this journal for last action, check `loop-state-machine.md` for the gate artifact. The `ds-state-surface.sh` hook surfaces most of this automatically if installed.

## Format (one block per entry)

```yaml
---
entry_id: v{N}-j{NNN}
timestamp: YYYY-MM-DDTHH:MM:SSZ
phase: FRAME | DGP | AUDIT | DATA_PREP | EDA | FEATURE_MODEL | VALIDATE | FINDINGS | MERGE | SHIP
branch: vN | vN.a | vN.b | ...
decision: <one-line summary of what was decided or tried>
reasoning: |
  Multi-line chain-of-thought.
  Why this over alternatives.
  What would disprove it.
alternatives_considered: []
artifacts_produced: []                # paths to runs/, findings/, audits/ that this entry produced
refs:
  findings: []                        # ids of findings this builds on or contradicts
  disproven: []
  dgp_predictions: []                 # P-NNN ids
  hypotheses: []                      # H-vN-XX ids
confidence: low | medium | high
open_questions: []
---
```

## Entries

<append new YAML blocks below; keep chronological order>
