# Templates and Naming

All starter templates live in `docs/llm/templates/`. Copy the relevant file when creating a new document.

## Available templates

| Template | Path | Use for |
| --- | --- | --- |
| Idea | `docs/llm/templates/idea.md` | Early concepts that may be promoted or rejected |
| Spec | `docs/llm/templates/spec.md` | Feature behavior, requirements, contracts |
| Acceptance (BDD) | `docs/llm/templates/acceptance.feature` | Gherkin acceptance scenarios for a spec |
| Plan | `docs/llm/templates/plan.md` | Implementation approach for a spec |
| ADR (light) | `docs/llm/templates/adr-light.md` | Small or obvious decisions |
| ADR (standard) | `docs/llm/templates/adr-standard.md` | Decisions with real alternatives |
| ADR (full) | `docs/llm/templates/adr-full.md` | Major architectural decisions |
| Roadmap | `docs/llm/templates/roadmap.md` | Now / Next / Later horizon pages |
| Runbook | `docs/llm/templates/runbook.md` | Operations when `docs/runbooks/` exists |
| Reference | `docs/llm/templates/reference.md` | CLI/API/config reference when added |
| Architecture overview | `docs/llm/templates/architecture.md` | Single whole-system overview: how it works, requirements, modes |
| Index | `docs/llm/templates/index.md` | Per-directory file listing for `docs/adr/`, `docs/specs/`, `docs/ideas/`, `docs/plans/`, `docs/roadmap/` |

## File naming

| Type | Pattern | Example |
| --- | --- | --- |
| ADR | `NNNN-short-title.md` | `0001-use-sqlite.md` |
| Idea | `YYYYMMDD-short-idea-name.md` | `20260707-cache-invalidation.md` |
| Spec | `YYYYMMDD-short-feature-name.md` | `20260707-cli-init.md` |
| Acceptance (BDD) | `features/YYYYMMDD-short-feature-name.feature` | `features/20260707-cli-init.feature` |
| Plan (active) | `YYYYMMDD-short-feature-name.md` | `20260707-cli-init.md` |
| Plan (completed) | `YYYYMMDD-short-feature-name.completed.md` | `20260707-cli-init.completed.md` |
| Plan (revision) | `YYYYMMDD-short-feature-name-v2.md` | `20260707-cli-init-v2.md` |
| Roadmap (horizon page) | `now.md` / `next.md` / `later.md` | `now.md` |
| Runbook | `short-operation-name.md` | `local-development.md` |
| Reference | `short-topic-name.md` | `cli-commands.md` |
| Architecture overview | `architecture.md` (fixed name, one per repo) | `architecture.md` |
| Index | `INDEX.md` (fixed name, one per directory) | `docs/adr/INDEX.md` |

Use lowercase kebab-case for new files unless an existing convention differs.

Prefix Idea, Spec, and Plan filenames with the creation date (`YYYYMMDD-`) so a plain directory listing sorts chronologically. Use the date the file is first created; do not change it on later edits.

ADR numbers are sequential and monotonic — never reuse a number. Do not date-prefix ADRs: the number is a stable citation ID (`ADR-0003`), and a date would still need a counter to disambiguate same-day ADRs.

Acceptance files live under `docs/specs/features/`, not directly in `docs/specs/` — this keeps prose specs scannable as the number of specs grows. Use the same base name as the spec it covers, date prefix included.

## Document structure

Use markdown sections for metadata. Do not use YAML frontmatter.

Common sections:

- `## Status` — document lifecycle state
- `## Related` — links to related Ideas, specs, plans, or ADRs

### Status values

| Document | Status values |
| --- | --- |
| Idea | `draft`, `accepted`, `rejected` |
| Spec | `draft`, `accepted`, `deprecated` |
| Plan | `draft`, `active`, `completed`, `superseded` |
| ADR | `proposed`, `accepted`, `deprecated`, `superseded` |
| Roadmap | `draft`, `active` |
| Architecture overview | `current`, `stale` |

## Per-directory INDEX.md

`docs/adr/`, `docs/specs/`, `docs/ideas/`, `docs/plans/`, and `docs/roadmap/` each keep an
`INDEX.md` listing the files inside, so an agent can scan the directory without opening
every file (see `docs/adr/0007-per-directory-index-md-hand-maintained-no-frontmatter.md`).

- Copy `docs/llm/templates/index.md` the first time a directory gets its first file.
- When creating or updating a file in one of these directories, add or update its row in
  that directory's `INDEX.md` (file link, title from the `# ` heading, status from
  `## Status`).
- Do not create an `INDEX.md` for an empty directory — add it alongside the first real file.
- `INDEX.md` is hand-maintained, not generated; keep it in sync as part of the same edit
  that touches the directory, not as a separate pass.

## Update semantics

- Prefer editing the smallest relevant section.
- Keep prior decisions visible; do not rewrite history unless correcting errors.
- Link related Ideas, specs, plans, and ADRs in `## Related`.
