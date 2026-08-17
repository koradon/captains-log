# Documentation Map

This repository uses a docs-as-code layout bootstrapped by [adrlane](https://github.com/koradon/adrlane).

## Structure

| Path | Purpose |
| --- | --- |
| `docs/specs/` | Feature specifications, behavior, and contracts |
| `docs/plans/` | Implementation plans derived from specs |
| `docs/adr/` | Architecture and design decision records |
| `docs/ideas/` | Early concepts that may be promoted to specs |
| `docs/roadmap/` | Now / Next / Later horizons for future initiatives |
| `docs/llm/` | Agent-facing documentation contract and templates |

## How this documentation grows

`adrlane init` creates a minimal core and does not predict future project shape.

When the project gains a new, recurring documentation need (for example CLI reference, runbooks, or API reference), the agent should:

1. Add a new top-level folder under `docs/` when the content does not fit `specs/`, `plans/`, `adr/`, `ideas/`, or `roadmap/`.
2. Copy a starter template from `docs/llm/templates/` and adapt it.
3. Update this file to document the new section.

Do not create empty folders "for later". Grow the tree only when there is real content to place there.

Release history lives in Git and release tooling, not in `docs/`.

For the full growth model, see the [adrlane documentation model](https://github.com/koradon/adrlane#documentation-model).

## For agents

Read `docs/llm/AGENT_PROTOCOL.md` first. It defines the doc workflow (`idea -> spec -> plan`) and how to extend the documentation consistently.
