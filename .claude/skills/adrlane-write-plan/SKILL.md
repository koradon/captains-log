---
name: adrlane-write-plan
description: >-
  Use when planning implementation of a spec across multiple steps or sessions, or when
  the user asks to write or update a plan in docs/plans/.
---

# Write a plan (adrlane)

Create or update a file under `docs/plans/`.

1. Read `docs/llm/DECISION_RULES.md` (Plan section) and `docs/llm/AGENT_PROTOCOL.md`.
2. Copy `docs/llm/templates/plan.md` for new plans.
3. Link to the driving spec in `## Related`.
4. Use `## Status` and `## Related` sections — no YAML frontmatter.
5. When finished, set status to `completed` and optionally rename with a `.completed` suffix.
