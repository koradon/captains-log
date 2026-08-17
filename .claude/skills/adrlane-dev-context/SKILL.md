---
name: adrlane-dev-context
description: >-
  Use when implementing features, refactoring, fixing bugs, or changing behavior.
  Read related specs in docs/specs/ before coding. After substantial changes,
  check whether specs, plans, or ADRs need updates per docs/llm/DECISION_RULES.md.
  When the conversation settles on a significant decision (architecture, technology
  choice, cross-cutting convention), propose capturing it as an ADR before continuing.
---

# Development context (adrlane)

This repository uses an [adrlane](https://github.com/koradon/adrlane) documentation layout.

## Before coding

1. Read `docs/README.md` for the documentation map.
2. Search `docs/specs/` for a related spec; read it before changing behavior.
3. Follow `docs/llm/AGENT_PROTOCOL.md` for workflow and write scope (`docs/**` only).
4. If `.adrlane/workspace.yaml` exists at the workspace root, follow `adrlane-workspace-routing` to choose project vs service doc paths.

## During and after work

- After substantial behavior or architecture changes, check `docs/llm/DECISION_RULES.md` for whether a spec, plan, or ADR needs updating.
- Prefer patching existing docs over creating duplicates.

## Significant decisions in conversation

When the discussion settles on an important decision (architecture, long-lived technology choice, cross-cutting convention):

1. Check ADR criteria in `docs/llm/DECISION_RULES.md`.
2. **Propose** capturing it in `docs/adr/` before moving on.
3. If the user agrees, use `docs/llm/templates/adr-*.md` (see the `adrlane-write-adr` skill).

Do not silently write ADRs without user acknowledgment unless they explicitly asked you to document the decision.
