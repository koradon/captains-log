# Decision Rules

Agents decide whether documentation needs updating during normal development work. Use these guidelines.

## Idea (`docs/ideas/`)

Create or update an idea when:

- you are exploring a potential change but the behavior/contracts are not fully defined yet
- you need to clarify problem, audience/value, options, constraints, and explicit no-gos

An idea answers **what outcome you're considering** and **whether it's worth pursuing**. Copy the template from `docs/llm/templates/idea.md`.

Promote an idea to a spec when behavior/contracts are clear. If it should not proceed, set `## Status` to `rejected`.

## Spec (`docs/specs/`)

Create or update a spec when a change affects:

- feature behavior or user-visible functionality
- public APIs, CLI behavior, or integration contracts
- data formats or boundaries between components

A spec answers **what** should be true. Copy the template from `docs/llm/templates/spec.md`.

## Plan (`docs/plans/`)

Create a plan when:

- implementation of a spec spans multiple steps or modules
- work will continue across sessions and needs a tracked approach
- there are meaningful risks, dependencies, or sequencing decisions

A plan answers **how** to build what the spec describes. Copy from `docs/llm/templates/plan.md`.

Skip a plan for small, obvious changes that a spec alone can describe.

When finishing a plan, set status to `completed` and optionally rename with a `.completed` suffix.

## ADR (`docs/adr/`)

Create an ADR when a change affects:

- system architecture or major component boundaries
- technology choices with long-term impact
- cross-cutting conventions other contributors must follow

An ADR answers **why** a decision was made. Choose a template tier:

| Tier | Template | Use when |
| --- | --- | --- |
| light | `docs/llm/templates/adr-light.md` | Obvious or local decisions with little debate |
| standard | `docs/llm/templates/adr-standard.md` | Real alternatives existed; medium impact |
| full | `docs/llm/templates/adr-full.md` | Architecturally significant, hard to reverse |

Propose a tier; the developer may correct it.

Number ADRs sequentially (`0001-short-title.md`). Do not reuse numbers. When superseding a decision, add a new ADR and link to the replaced one.

## Roadmap (`docs/roadmap/`)

Create or update roadmap docs when you need a shared view of future initiatives without exact dates.

Use the Now / Next / Later horizons and link each roadmap item to related Idea / Spec / Plan docs.

If you need more detailed horizon pages beyond `docs/roadmap/README.md`, copy from `docs/llm/templates/roadmap.md` and adapt it.

## Extending the documentation tree

Add a new top-level folder under `docs/` when:

- a new, recurring content type appears (for example operations runbooks or CLI reference)
- the content does not fit `specs/`, `plans/`, `adr/`, `ideas/`, or `roadmap/`

When adding a section:

1. Pick or adapt a template from `docs/llm/templates/`.
2. Add a `_template` or starter file in the new folder if helpful.
3. Update `docs/README.md`.

## General rule

If unsure, add a short note to the most relevant existing doc rather than creating a new top-level artifact.
