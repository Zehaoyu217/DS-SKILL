# Research Program — {project name}

> **What this file is:** The user's directional research judgment — which hypotheses
> you believe are promising, which features/models are worth trying, and what directions
> you want explored. This is "what to try", not "how to work."
>
> **What this file is NOT:** Operational settings (verbosity, overrides) — those go in
> `USER_GUIDANCE.md`.
>
> **When it is read:** By the orchestrator at FRAME entry and FEATURE_MODEL entry.
> Passed as advisory context to Explorer subagent dispatch (Explorer may note your
> nominees but is not required to explore every one).
>
> **How to update:** Edit directly. Append to "Version history" when an item is tested.

---

## Active hypotheses (user's priors)

<!-- List hypotheses you believe are worth testing, in rough priority order.
     These seed the brainstorm — they do not replace the Skeptic micro-audit.
     Explorer is still dispatched independently without seeing this file first.

     Format: H-rp-NNN | <statement> | <expected direction> | <why you believe this>
-->

<!-- Example:
H-rp-001 | Higher recency of last transaction predicts churn | positive | domain knowledge from prior project
H-rp-002 | Interaction between tenure and plan_type matters | unclear | exploratory
-->

---

## Feature candidates (user's nominees)

<!-- Features or feature families you want the Explorer to consider.
     Not pre-committed — Explorer and Skeptic may reject or extend these.

     Format: - <feature description> | <why you think it matters>
-->

<!-- Example:
- days_since_last_login rolling 7d/30d/90d | user engagement signal
- ratio of failed_payments to total_payments | financial stress proxy
-->

---

## Model candidates (user's nominees)

<!-- Model families or architectures you want tried.
     Subject to Skeptic micro-audit like any other brainstorm candidate.
     These are nominees, not mandates.

     Format: - <model name> | <why>
-->

<!-- Example:
- LightGBM | fast, handles categoricals natively, good on tabular
- TabNet | worth checking for feature attribution clarity
-->

---

## Excluded approaches (user's vetoes)

<!-- Approaches you do NOT want tried, with brief rationale.
     Honored unless an iron law requires them (e.g., a linear baseline is required by
     Iron Law #5 regardless of vetoes — such conflicts are noted in the step-journal).

     Format: - <approach> | <reason>
-->

<!-- Example:
- Neural networks | latency constraint, must be <50ms inference
- Target encoding without CV | we got burned by this last project
-->

---

## Version history (append-only)

<!-- Orchestrator appends a summary of which research-program items were tested each
     version and what happened to them. Never edit past entries.

     Format:
     ### v{N} — {date}
     - H-rp-001: tested as H-vN-02 → disproven/v1-d001.md
     - Feature candidate "days_since_last_login": included in brainstorm-FEATURE_ENG as A2 → finding/v1-f002.md
     - Model candidate "TabNet": screen-rejected (below threshold) in screen-results.json
-->
