---
name: adrlane-write-architecture-overview
description: >-
  Use when asked to explain, document, or generate an architecture overview of the
  current project, or proactively after a change that alters module boundaries,
  execution flow, or requirements to run. Creates or refreshes docs/architecture.md.
---

# Write an architecture overview (adrlane)

Create or refresh the single file `docs/architecture.md`.

1. Read `docs/llm/DECISION_RULES.md` (Architecture overview section) and `docs/llm/AGENT_PROTOCOL.md`.
2. If `docs/architecture.md` does not exist, copy `docs/llm/templates/architecture.md`. If it exists, patch only the sections that are stale — do not rewrite the whole file.
3. Investigate the actual project before writing: entry points, manifest/lockfile, module boundaries, existing specs and ADRs. Do not guess or assume another project's stack.
4. Cover, at minimum: purpose, requirements to run, execution flow, subsystems, data/storage model, modes/entry points, and design principles.
5. Include as many Mermaid diagrams as needed to make the system's shape clear (module map, data/request flow, deployment) — no fixed count, and no diagram for its own sake.
6. Use `## Status` and `## Related` sections — no YAML frontmatter.
7. When you create the file for the first time, add a row for it to `docs/README.md`'s structure table.
