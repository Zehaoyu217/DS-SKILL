# Dashboard Spec

## Purpose
Always-open browser page; persistent visual log. Shows every modeled run since project inception until the user manually deletes.

## Disk layout (inside `ds-workspace/dashboard/`)

```
index.html
assets/
  styles.css
  app.js
  charts.js
  vendor/uPlot.min.js
data/
  leaderboard.json    # source of truth (validates against templates/leaderboard.schema.json)
  events.ndjson       # append-only audit log, one JSON per line
URL.txt               # written by server at startup
```

## Serving
- `server/serve_dashboard.py` picks a free port, serves `dashboard/` over HTTP, writes URL to `URL.txt`, writes PID to `.dashboard-server.pid`.
- Orchestrator attempts `open <url>` on macOS.
- Polling: page fetches `data/leaderboard.json` every 3000 ms.
- Orchestrator kills the server on `ship` or `abort`.

## Writer contract (orchestrator's responsibility)

On every run/event mutation the orchestrator MUST:

1. Update `leaderboard.json` using write-temp-then-rename (atomic).
2. Append one JSON line to `events.ndjson`.

Runs that never appear in `leaderboard.json` do not exist (Iron Law #11). FEATURE_MODEL and VALIDATE exits block without a dashboard entry for the current run.

## UI sections

1. **Headline band** — current winner: model, primary metric with CI, lift vs baseline, date.
2. **Leaderboard table** — all runs, sortable; color-coded by status (`valid` / `superseded` / `invalidated`); row click opens drawer with `params_summary`, `feature_groups`, `seed`, `data_sha256`.
3. **Version timeline** — horizontal vN strip with phase chips and event markers.
4. **Metric-over-time chart** — uPlot; one line per `model` family; uncertainty band from `cv_std`; dashed baseline reference.
5. **Disproven wall** — card grid of `disproven[]`; "museum of wrong ideas".
6. **Audit strip** — latest Skeptic / Validation Auditor / Statistician verdicts + any open CRITICAL blockers.

## Design discipline

- Editorial/bento direction. Not a dashboard-by-numbers template.
- Palette via `oklch()` CSS custom properties; dark-luxury default.
- Typography pairing: serif display for the headline metric; mono for numbers; system sans for body.
- Animation only on `transform`/`opacity`.
- Bundle budget: **< 80 kB gzipped total**. Stack: vanilla JS + uPlot (~40 kB). No React, no Tailwind.
- Semantic HTML: `<header>`, `<main>`, `<section aria-labelledby="...">`.
- Reduced-motion respected.
