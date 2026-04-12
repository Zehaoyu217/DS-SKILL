# Checklist: Reproducibility

Engineer signs. Gate for VALIDATE exit and ship. Iron Law #9.

## Per-run required files (inside `runs/vN/`)
- [ ] `seed.txt` — integer seed used for RNG
- [ ] `env.lock` — pinned dependency snapshot (pip freeze / uv lock / poetry lock)
- [ ] `data.sha256` — hash of the exact training frame used (excluding holdout)
- [ ] `metrics.json` — CV mean/std/ci, lift vs baseline

## Random-fold re-run
- [ ] Pick one CV fold deterministically from the seed.
- [ ] Re-run using `env.lock` and the recorded seed.
- [ ] Compare new metric to the stored one within numerical `tol` (default 1e-6 for deterministic frameworks, 1e-3 for GPU/non-deterministic).
- [ ] Mismatch beyond tolerance → Engineer BLOCK. Document non-determinism source.

## Hygiene
- [ ] No module-level execution in `src/` (functions/classes only).
- [ ] No `pd.DataFrame()` construction with literal data from notebooks into `src/` models.
- [ ] No `TODO`/`FIXME` in code paths hit during the run.

## Persona
Engineer writes `audits/vN-repro.md`.
