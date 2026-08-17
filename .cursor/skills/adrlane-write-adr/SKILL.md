---
name: adrlane-write-adr
description: >-
  Use when documenting a significant decision, or when the user agrees to capture a
  conversation decision as an ADR in docs/adr/. Choose adr-light, adr-standard, or
  adr-full per docs/llm/DECISION_RULES.md.
---

# Write an ADR (adrlane)

Create or update a file under `docs/adr/`.

1. Read `docs/llm/DECISION_RULES.md` (ADR section) and `docs/llm/AGENT_PROTOCOL.md`.
2. Choose a template tier:
   - `docs/llm/templates/adr-light.md` — obvious or local decisions
   - `docs/llm/templates/adr-standard.md` — real alternatives, medium impact
   - `docs/llm/templates/adr-full.md` — significant, hard to reverse
3. Number sequentially: `0001-short-title.md` (do not reuse numbers).
4. Use `## Status` and `## Related` sections — no YAML frontmatter.
5. When superseding a decision, add a new ADR and link to the replaced one.
