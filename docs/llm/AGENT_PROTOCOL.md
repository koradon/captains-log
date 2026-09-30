# Agent Protocol

This file is the canonical, agent-agnostic contract for working with documentation in this repository.

## Agent skills (installed by `adrlane init`)

If this repository was bootstrapped with adrlane, agent-specific skills may be present:

| Skill | Role |
| --- | --- |
| `adrlane-dev-context` | Ambient: read specs before coding; propose ADRs after significant decisions |
| `adrlane-write-idea` | Write or update ideas in `docs/ideas/` |
| `adrlane-write-spec` | Write or update specs in `docs/specs/` |
| `adrlane-write-plan` | Write or update plans in `docs/plans/` |
| `adrlane-write-adr` | Document decisions in `docs/adr/` |
| `adrlane-write-architecture-overview` | Create or refresh the whole-system overview in `docs/architecture.md` |
| `adrlane-workspace-routing` | Route docs to project or sub-repo trees when `.adrlane/workspace.yaml` exists |

Skills are thin adapters; this file and `docs/llm/DECISION_RULES.md` remain the source of truth.

## Who decides when to update

The agent decides whether documentation needs updating during normal development. There is no adrlane sync job or gap detector. When behavior, decisions, or structure change in a way that should be recorded, use the installed skills and this contract to create or patch files under `docs/`. The developer reviews changes via `git diff` and commits.

## Where documentation lives

| Type | Location | When to use |
| --- | --- | --- |
| Idea | `docs/ideas/` | Early, uncommitted concepts that may be promoted to a spec |
| Spec | `docs/specs/` | What the system should do — requirements, behavior, contracts |
| Plan | `docs/plans/` | How to implement a spec — steps, scope, risks |
| ADR | `docs/adr/` | Why a significant decision was made and what it implies |
| Architecture overview | `docs/architecture.md` | How the whole system works today — requirements, execution flow, modules, diagrams |
| Roadmap | `docs/roadmap/` | Now / Next / Later horizons for future initiatives |

Other sections (for example `docs/runbooks/`, `docs/reference/`) are added by the agent when the project needs them. See `docs/README.md`.

## Idea → spec → plan workflow

1. Write or update an **idea** when exploring a potential change that is not yet fully specified.
2. Promote an accepted idea to a **spec** when desired behavior and contracts are clear.
3. For accepted specs, keep Gherkin acceptance scenarios in `docs/specs/features/<spec-slug>.feature`.
4. Create a **plan** from the spec when implementation spans multiple steps, modules, or sessions.
5. Small changes may use a spec alone — a plan is not required for every spec.
6. Link ideas, specs, and plans in a `## Related` section.
7. When a plan is finished, set `## Status` to `completed` and optionally rename the file with a `.completed` suffix (for example `cli-init.completed.md`).
8. When an idea is rejected, set `## Status` to `rejected` (and optionally link to the alternative decision, if any).

## Before writing

1. Read `docs/README.md` for the current documentation map.
2. Search existing docs for related context.
3. Prefer updating an existing artifact over creating a duplicate.
4. Read `docs/llm/TEMPLATES.md` for naming conventions and available templates.

## How to update

- **Create** a new file when no suitable artifact exists.
- **Patch** specific sections when correcting or extending existing docs.
- **Extend structure** by adding new top-level folders only when needed, then update `docs/README.md`.

Never delete unrelated documentation.

## Write scope

When updating documentation, change files under `docs/**` only.

## Style

Follow `docs/llm/DOC_GUIDELINES.md` for language, tone, and formatting.
