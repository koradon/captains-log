# Ideas

Ideas are early, uncommitted concepts. The goal is to decide whether a concept deserves further investment.

An idea can flow into:

- a **Spec** (`docs/specs/`) when the desired behavior and contracts become clear
- a **Plan** (`docs/plans/`) when implementation needs multiple steps or sessions

If an idea does not pass evaluation, the agent may set `## Status` to `rejected` (and optionally link what was decided instead).

## Common flow

1. Create/update an idea in `docs/ideas/`.
2. When the behavior is clear enough, create a spec in `docs/specs/` and link them in `## Related`.
3. When implementation is non-trivial, create a plan in `docs/plans/` and link it from the spec.

## Template

Copy and adapt `docs/llm/templates/idea.md`.

## How to stay agnostic

Ideas describe outcomes and constraints without assuming a specific stack (web, backend, CLI, or binaries).
