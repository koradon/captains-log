---
name: adrlane-write-spec
description: >-
  Use when defining requirements, feature behavior, API or CLI contracts, or when the
  user asks to write or update a spec in docs/specs/. Create Gherkin acceptance
  scenarios in docs/specs/features/<slug>.feature when behavior should be acceptance-tested.
---

# Write a spec (adrlane)

Create or update a file under `docs/specs/`.

1. Read `docs/llm/DECISION_RULES.md` (Spec section) and `docs/llm/AGENT_PROTOCOL.md`.
2. Copy `docs/llm/templates/spec.md` for new specs.
3. For accepted behavior, add or update a Gherkin file: `docs/specs/features/<spec-slug>.feature` using `docs/llm/templates/acceptance.feature`.
4. Use `## Status` and `## Related` sections — no YAML frontmatter.
5. Link from related ideas, plans, or roadmap entries in `## Related`.
