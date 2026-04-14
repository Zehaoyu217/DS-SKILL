# Playbook: Collaborative Brainstorm (`brainstorm` command)

Triggered when the user types `brainstorm` or `brainstorm <topic>` at any phase.
This is on-demand and user-initiated — not automatic at every version start.

Style: listen first (understand what the user is thinking), then structure
(propose 2-3 approaches with trade-offs and Plan B for each).

---

## Step 0 — Surface context (silent, before responding)

Read and load into working context:
- `state.json` → current phase, version, mode
- `plans/vN.md` YAML `hypotheses:` block → active hypothesis ids and statements
- Last 3 entries from `step-journal/vN.md` → recent decisions and their reasoning
- `USER_GUIDANCE.md` → active G-NNN entries (user's current stated intent)
- `lessons.md` → 2-3 entries most relevant to the topic (if topic was given)
  Skip lessons with `superseded_by` set. Skip lessons inapplicable to current mode/context.

Do NOT narrate this step. The context card in Step 1 summarizes what was found.

---

## Step 1 — Open the floor

Output the context card followed by the open question. Nothing else in this message.

```
━━ Brainstorm session ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase: {phase}  |  v{N}  |  {mode} mode
{if topic given → "Topic: {topic}"}
Active hypotheses: {H-vN-XX: one-line statement, …  — or "(none yet)"}
Relevant lessons: {L-vN-NNN: one-line slug, …  — or "(none relevant yet)"}
Active guidance: {most recent G-NNN text — or "(none)"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What are you thinking? (What's the decision, concern, or idea you want to work through?)
```

---

## Step 2 — Up to 2 clarifying questions (one at a time)

After the user responds:
- If the core concern and success criterion are clear → skip to Step 3 immediately.
- If unclear → ask at most 1 clarifying question, wait for the response.
- After that response → ask at most 1 more if still unclear, then proceed to Step 3
  regardless. If you must assume, state the assumption explicitly at the top of Step 3.

Useful clarifying questions (pick the most relevant one):
- "What would a good result look like here?" → surfaces success criterion
- "What's your main concern with the current approach?" → surfaces the actual problem
- "Is there a specific constraint I should design around?" → surfaces hidden blockers

---

## Step 3 — Structured proposal

Present 2-3 candidate approaches. Each gets the same structure.

If assumptions were made in Step 2, open with:
> "Assuming {assumption} — let me know if that's wrong and I'll revise."

### Approach format

```markdown
## Approach A — {short name}

**What it is:** {1 paragraph — what this approach does, concretely. No vague descriptions.}

**Why it might work:** {mechanism, prior evidence, or relevant lesson reference (apply knowledge-lint first)}

**Why it might fail:** {specific failure modes or known limitations — be concrete}

**Kill criterion:** {what result would mean "this approach failed"? Quantitative where possible.}

**Plan B if this fails:** Fall back to Approach {B or C} because {one-line rationale}.
Trigger: {what observation would prompt the switch?}
```

Repeat for Approach B and C.

Then close with:

```markdown
## My recommendation: Approach {A|B|C}

{2-3 sentences comparing trade-offs explicitly. Name the trade-off; do not just say "it's better."}

What would change my recommendation: {what information or result would make B or C the better pick?}
```

### Rules for approach generation

- **A1 ≠ "first thing that came to mind"** — if one approach is clearly dominant, either
  reframe the decision so there is a real choice, or include explicitly weaker alternatives
  and label them as such with reasoning for why they are included.
- **Lessons inform, don't dictate** — cite relevant lessons as evidence but apply
  knowledge-lint (Protocol 1 in `playbooks/human-in-the-loop.md`) before citing.
  Only cite lessons that apply to this specific context.
- **Plan B must be concrete** — "try something else" is not a Plan B. Name the approach
  and the specific kill criterion that triggers the fallback.
- **Active guidance takes priority** — if `USER_GUIDANCE.md` shows active guidance pointing
  toward a specific direction, incorporate it into Approach A. If you recommend against it,
  explain why explicitly and let the user decide.

---

## Step 4 — User picks or redirects

### User picks an approach

1. Write `runs/vN/brainstorm-vN-USER-{topic}.md` using `templates/brainstorm-vN.md`.
   Set in the YAML frontmatter:
   - `triggered_by: user-collab`
   - `chosen_alternative_id:` the user's chosen approach letter (A/B/C)
   - `contingency_alternative_id:` the Plan B from that approach
   - `alternatives_count:` number of approaches presented
2. Confirm: "Written to `runs/vN/brainstorm-vN-USER-{topic}.md`. This will surface at the
   next relevant gate as an alternative to the auto-generated brainstorm."
3. Proceed to Step 5.

### User redirects

Acknowledge the redirect. Update your framing. Loop back to Step 3 with the new direction.
Do not re-present options the user has already dismissed.

---

## Step 5 — Anchor (optional)

If the session produced a clear directional decision:
1. Append a G-NNN entry to `USER_GUIDANCE.md`:
   ```
   ### G-{NNN} — {timestamp}
   **User said:** "go with {approach name} for {topic}"
   **Agent interpretation:** user has chosen {approach name}; treat as active guidance for {phase}
   **Status:** active
   **Supersedes:** (none) | G-{prior if superseding}
   ```
2. Update `## Current focus` → `last_updated`.

If the session was exploratory (no clear decision), do NOT append a G-NNN entry.

---

## Notes

- The user-collab brainstorm artifact (`brainstorm-vN-USER-{topic}.md`) is separate from
  auto-generated brainstorms (`brainstorm-vN-DATA_PREP.md`, etc.). At a phase gate, both
  are available — the user-collab version can replace or supplement the auto-generated one.
- If `verbosity: quiet`, still run the full brainstorm session — verbosity only suppresses
  decision narration checkpoints (Protocol 2), not interactive sessions.
- The brainstorm session does NOT count as a phase transition. No gate files are written
  by the session itself. Gate files are written when the chosen approach is executed.
